# routes/records.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app, Response
)
from extensions import db
from models import Item
import io
import csv
from datetime import datetime, timezone, timedelta
from sqlalchemy import func

# try to use zoneinfo for accurate tz handling; fallback to fixed offset
try:
    from zoneinfo import ZoneInfo
    KOLKATA_TZ = ZoneInfo('Asia/Kolkata')
    def to_ist(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            # assume stored in UTC if naive
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KOLKATA_TZ)
except Exception:
    IST_OFFSET = timedelta(hours=5, minutes=30)
    def to_ist(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone(IST_OFFSET))


records_bp = Blueprint('records', __name__)


def _build_query(q, group):
    base = Item.query
    if q:
        like = f"%{q}%"
        base = base.filter(
            (Item.description.ilike(like)) |
            (Item.supplier.ilike(like)) |
            (Item.item_group.ilike(like))
        )
    if group:
        base = base.filter(Item.item_group == group)
    return base


def _distinct_groups():
    try:
        rows = db.session.query(Item.item_group).filter(Item.item_group.isnot(None)).distinct().order_by(Item.item_group).all()
        return [r[0] for r in rows if r[0] is not None and str(r[0]).strip() != ""]
    except Exception:
        return []


@records_bp.route('/records', methods=['GET'])
def records():
    q = request.args.get('q', '').strip()
    group_selected = request.args.get('group', '').strip()
    fmt = request.args.get('format', '').lower()

    # CSV export (server-side)
    if fmt == 'csv':
        try:
            ids_param = request.args.get('ids', '').strip()
            if ids_param:
                try:
                    id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
                except Exception:
                    id_list = []
                query = Item.query.filter(Item.id.in_(id_list)).order_by(Item.id.desc())
            else:
                query = _build_query(q, group_selected).order_by(Item.id.desc())

            items = query.all()
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            writer.writerow([
                "SN", "id", "description", "item_group", "mrp", "item_size",
                "main_unit", "alt_unit", "alt_qty", "purc_price",
                "bulk_sp1", "bulk_sp2", "sale_price", "supplier", "last_updated_ist"
            ])
            for idx, it in enumerate(items, start=1):
                last = getattr(it, 'last_updated', None)
                last_s = ''
                if last:
                    try:
                        last_s = to_ist(last).strftime('%d-%m-%Y (%I:%M %p)')
                    except Exception:
                        last_s = last.isoformat(sep=' ')
                writer.writerow([
                    idx,
                    it.id,
                    it.description or '',
                    it.item_group or '',
                    (it.mrp if it.mrp is not None else ''),
                    it.item_size or '',
                    it.main_unit or '',
                    it.alt_unit or '',
                    (it.alt_qty if it.alt_qty is not None else ''),
                    (f"{it.purc_price:.2f}" if it.purc_price is not None else ''),
                    (f"{it.bulk_sp1:.2f}" if it.bulk_sp1 is not None else ''),
                    (f"{it.bulk_sp2:.2f}" if it.bulk_sp2 is not None else ''),
                    (f"{it.sale_price:.2f}" if it.sale_price is not None else ''),
                    it.supplier or '',
                    last_s
                ])
            csv_text = output.getvalue()
            output.close()
            csv_bytes = csv_text.encode('utf-8-sig')
            filename = f"items_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            return Response(
                csv_bytes,
                mimetype="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment;filename={filename}", "Content-Length": str(len(csv_bytes))}
            )
        except Exception as e:
            current_app.logger.exception("CSV export failed")
            flash(f"Could not export CSV: {e}", "danger")
            return redirect(url_for('records.records'))

    # HTML listing with pagination
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 12))
    except ValueError:
        per_page = 12
    per_page = max(5, min(per_page, 200))

    query = _build_query(q, group_selected).order_by(Item.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    # Prepare IST display string for each item (server-side)
    for it in items:
        it.last_updated_ist = ''
        if getattr(it, 'last_updated', None):
            try:
                dt_ist = to_ist(it.last_updated)
                it.last_updated_ist = dt_ist.strftime('%d-%m-%Y (%I:%M %p)')
            except Exception:
                try:
                    it.last_updated_ist = it.last_updated.isoformat(sep=' ')
                except Exception:
                    it.last_updated_ist = ''

    groups = _distinct_groups()

    return render_template(
        'records.html',
        items=items,
        q=q,
        pagination=pagination,
        groups=groups,
        group_selected=group_selected
    )


@records_bp.route('/records/import', methods=['POST'])
def import_items():
    """
    Accepts a file upload (CSV or XLSX). Expects headers or well-formed columns.
    Skips duplicates by matching normalized description (case-insensitive, whitespace-normalized).
    Returns JSON with counts: total, imported, skipped, errors (and example messages).
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    filename = file.filename or ''
    lower = filename.lower()
    rows = []
    total = 0
    imported = 0
    skipped = 0
    errors = 0
    skipped_examples = []

    # helper to normalize description for duplicate checks
    def norm_desc(s):
        if s is None:
            return ''
        return ' '.join(str(s).strip().split()).lower()

    try:
        if lower.endswith('.xlsx') or lower.endswith('.xlsm') or lower.endswith('.xls'):
            try:
                import openpyxl
            except Exception:
                return jsonify({"success": False, "message": "Missing dependency openpyxl. Run: pip install openpyxl"}), 500
            wb = openpyxl.load_workbook(file.stream, read_only=True, data_only=True)
            ws = wb.active
            data = list(ws.values)
            if not data:
                return jsonify({"success": False, "message": "Spreadsheet is empty."}), 400
            header = [str(h).strip().lower() if h is not None else '' for h in data[0]]
            for r in data[1:]:
                row = {header[i]: (r[i] if i < len(r) else None) for i in range(len(header))}
                rows.append(row)
        else:
            # assume CSV
            # decode to text
            txt = file.stream.read().decode('utf-8-sig')  # tolerate BOM
            reader = csv.reader(io.StringIO(txt))
            data = list(reader)
            if not data:
                return jsonify({"success": False, "message": "CSV is empty."}), 400
            header = [h.strip().lower() for h in data[0]]
            for r in data[1:]:
                # map header to row values (safe)
                row = {}
                for i, h in enumerate(header):
                    row[h] = r[i] if i < len(r) else None
                rows.append(row)
    except Exception as e:
        current_app.logger.exception("Import parse failed")
        return jsonify({"success": False, "message": f"Failed to read uploaded file: {e}"}), 400

    # Normalize header keys mapping to model fields we accept
    # Accept common column names -> field names
    key_map_candidates = {
        'description': ['description', 'item description', 'name', 'item_name'],
        'item_group': ['item_group', 'group', 'category'],
        'mrp': ['mrp', 'price', 'mrp₹', 'mrp (₹)'],
        'item_size': ['item_size', 'size'],
        'main_unit': ['main_unit', 'main'],
        'alt_unit': ['alt_unit', 'alt'],
        'alt_qty': ['alt_qty','altqty','qty','quantity'],
        'purc_price': ['purc_price','purchase','purchase_price','purc_price'],
        'bulk_sp1': ['bulk_sp1','bsp1','bulk1'],
        'bulk_sp2': ['bulk_sp2','bsp2','bulk2'],
        'sale_price': ['sale_price','sale','selling_price'],
        'supplier': ['supplier','vendor']
    }

    # Build reverse map header_key -> canonical field
    header_to_field = {}
    sample_headers = set()
    if rows:
        sample_headers = set(str(k).strip().lower() for k in rows[0].keys())

    for field, cand in key_map_candidates.items():
        for c in cand:
            if c in sample_headers:
                header_to_field[c] = field

    # If header_to_field incomplete, try fuzzy: match by startswith/contains
    for h in sample_headers:
        if h in header_to_field:
            continue
        for field, cand in key_map_candidates.items():
            for c in cand:
                if c in h or h in c:
                    header_to_field[h] = field
                    break
            if h in header_to_field:
                break

    # For rows without headers (if rows are lists), try positional mapping by assuming order:
    # But in our implementation rows are dicts (from header), so skip positional.

    # fetch existing descriptions set for duplicate detection (lowercased normalized)
    existing = db.session.query(Item.id, Item.description).all()
    existing_norm = {norm_desc(r[1]): r[0] for r in existing if r[1]}

    # Process rows
    new_items = []
    for idx, r in enumerate(rows, start=1):
        total += 1
        try:
            # pull values by mapped fields
            def val_for(field):
                # find header that maps to this field
                for h, f in header_to_field.items():
                    if f == field:
                        v = r.get(h)
                        return v
                # fallback: try direct key equal to canonical name
                return r.get(field) if isinstance(r, dict) else None

            desc = val_for('description') or ''
            desc_norm = norm_desc(desc)
            # Skip empty description
            if not desc_norm:
                skipped += 1
                skipped_examples.append(f"Row {idx}: empty description")
                continue

            # Duplicate check by normalized description
            if desc_norm in existing_norm:
                skipped += 1
                skipped_examples.append(f"Row {idx}: duplicate '{desc}'")
                continue

            # parse numeric fields safely
            def num(x):
                if x is None or str(x).strip() == '':
                    return None
                try:
                    return float(str(x).replace(',','').strip())
                except Exception:
                    return None

            item = Item(
                description=str(desc).strip(),
                item_group=val_for('item_group') or '',
                mrp=(lambda v: (int(v) if str(v).strip().isdigit() else float(v)) if v is not None and str(v).strip()!='' else None)(val_for('mrp')) if val_for('mrp') is not None else None,
                item_size=(val_for('item_size') or '') ,
                main_unit=(val_for('main_unit') or ''),
                alt_unit=(val_for('alt_unit') or ''),
                alt_qty=(int(num(val_for('alt_qty'))) if num(val_for('alt_qty')) is not None else None),
                purc_price=(num(val_for('purc_price')) if val_for('purc_price') is not None else None),
                bulk_sp1=(num(val_for('bulk_sp1')) if val_for('bulk_sp1') is not None else None),
                bulk_sp2=(num(val_for('bulk_sp2')) if val_for('bulk_sp2') is not None else None),
                sale_price=(num(val_for('sale_price')) if val_for('sale_price') is not None else None),
                supplier=(val_for('supplier') or '')
            )
            db.session.add(item)
            # track to existing_norm so subsequent rows in same import won't be duplicated
            # (we don't have id until commit; use placeholder)
            existing_norm[desc_norm] = None
            new_items.append(item)
            imported += 1
        except Exception as ex:
            errors += 1
            current_app.logger.exception("Error importing row")
            skipped_examples.append(f"Row {idx}: error {ex}")

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.exception("Commit failed")
        db.session.rollback()
        return jsonify({"success": False, "message": f"DB commit failed: {e}"}), 500

    return jsonify({
        "success": True,
        "total": total,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "skipped_examples": skipped_examples[:10]
    })


@records_bp.route('/edit/<int:id>', methods=['GET'])
def edit_item(id):
    return redirect(url_for('add_item.add_item', id=id))


@records_bp.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error deleting item")
        flash(f'Error deleting item: {e}', 'danger')
    return redirect(url_for('records.records'))


@records_bp.route('/api/records', methods=['GET'])
def api_records():
    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        per_page = 20
    per_page = max(1, min(per_page, 200))

    query = _build_query(q, request.args.get('group', '').strip()).order_by(Item.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    def row_to_dict(it):
        last = getattr(it, 'last_updated', None)
        last_s = None
        if last:
            try:
                last_s = to_ist(last).isoformat(sep=' ')
            except Exception:
                last_s = last.isoformat(sep=' ')
        return {
            "id": it.id,
            "description": it.description,
            "item_group": it.item_group,
            "mrp": it.mrp,
            "item_size": it.item_size,
            "main_unit": it.main_unit,
            "alt_unit": it.alt_unit,
            "alt_qty": it.alt_qty,
            "purc_price": it.purc_price,
            "bulk_sp1": it.bulk_sp1,
            "bulk_sp2": it.bulk_sp2,
            "sale_price": it.sale_price,
            "supplier": it.supplier,
            "last_updated": last_s
        }

    return jsonify({
        "items": [row_to_dict(it) for it in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages
    })


@records_bp.route('/api/item/<int:id>', methods=['GET'])
def api_get_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Item not found"}), 404
    last = getattr(item, 'last_updated', None)
    last_s = None
    if last:
        try:
            last_s = to_ist(last).isoformat(sep=' ')
        except Exception:
            last_s = last.isoformat(sep=' ')
    return jsonify({
        "success": True,
        "item": {
            "id": item.id,
            "description": item.description,
            "item_group": item.item_group,
            "mrp": item.mrp,
            "item_size": item.item_size,
            "main_unit": item.main_unit,
            "alt_unit": item.alt_unit,
            "alt_qty": item.alt_qty,
            "purc_price": item.purc_price,
            "bulk_sp1": item.bulk_sp1,
            "bulk_sp2": item.bulk_sp2,
            "sale_price": item.sale_price,
            "supplier": item.supplier,
            "last_updated": last_s
        }
    })


@records_bp.route('/api/delete/<int:id>', methods=['POST'])
def api_delete_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found.'}), 404
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Deleted.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("API delete error")
        return jsonify({'success': False, 'message': str(e)}), 500
