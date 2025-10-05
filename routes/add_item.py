# routes/add_item.py
from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from extensions import db
from models import Item
import re
from datetime import datetime

add_item_bp = Blueprint('add_item', __name__)

def safe_int(v, default=0):
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == '':
            return default
        s = s.replace(',', '')
        return int(float(s))
    except Exception:
        return default

def safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == '':
            return default
        s = s.replace(',', '')
        return float(s)
    except Exception:
        return default

def extract_group(desc):
    if not desc:
        return ''
    m = re.search(r'\(([^)]+)\)', desc)
    return m.group(1).strip() if m else ''

def extract_mrp(desc):
    """
    Only take a number that directly prefixes a '/' or '/-' token.
    Example matches: '500/-', '500 / -', '500 /'
    Will NOT match '20ML' or numbers followed by letters.
    """
    if not desc:
        return 0
    m = re.search(r'(\d+(?:\.\d+)?)(?=\s*(?:\/-|\//|\/))', desc)
    if m:
        try:
            return int(float(m.group(1)))
        except Exception:
            return 0
    return 0

def extract_item_size(size):
    """
    Parse strings like '1CTN=20PKD' or '1 CTN = 20 PKD'
    Returns (main_unit, alt_unit, alt_qty) or ('','',0)
    """
    if not size:
        return ('', '', 0)
    s = size.strip()
    m = re.search(r'(\d+)\s*([A-Za-z]+)\s*=\s*(\d+)\s*([A-Za-z]+)', s, flags=re.I)
    if m:
        left_qty = int(m.group(1))
        main_unit = m.group(2).upper()
        right_qty = int(m.group(3))
        alt_unit = m.group(4).upper()
        return (main_unit, alt_unit, right_qty)
    return ('', '', 0)


@add_item_bp.route('/', methods=['GET', 'POST'])
@add_item_bp.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        item_id = request.form.get('id')
        try:
            # find existing or create new
            item = None
            if item_id:
                try:
                    item = Item.query.get(int(item_id))
                except Exception:
                    item = None
            if not item:
                item = Item()

            # raw inputs
            desc = (request.form.get('description') or '').strip()
            size = (request.form.get('item_size') or '').strip()

            # form-provided group and mrp (prefer these if non-empty)
            group_form = (request.form.get('item_group') or '').strip()
            mrp_form_raw = (request.form.get('mrp') or '').strip()

            # group: prefer explicit, else parse from desc
            group = group_form if group_form else extract_group(desc)

            # mrp: prefer explicit numeric form value, else parse from description
            if mrp_form_raw and re.search(r'\d', mrp_form_raw):
                mrp_val = safe_int(mrp_form_raw, 0)
            else:
                mrp_val = extract_mrp(desc)

            # Manual main/alt/qty from form (user typing) - these should take precedence over parsed values
            manual_main = (request.form.get('main_unit') or '').strip()
            manual_alt = (request.form.get('alt_unit') or '').strip()
            manual_qty_raw = (request.form.get('alt_qty') or '').strip()

            manual_main_up = manual_main.upper() if manual_main else ''
            manual_alt_up = manual_alt.upper() if manual_alt else ''
            manual_qty = safe_int(manual_qty_raw, None) if manual_qty_raw != '' else None

            # Parse item_size if present
            parsed_main, parsed_alt, parsed_qty = ('', '', 0)
            if size:
                parsed_main, parsed_alt, parsed_qty = extract_item_size(size)

            # Decide final main/alt/qty:
            # - If user provided manual value (non-empty), use it (manual wins)
            # - Else, if parsed value exists (non-empty), use parsed
            # - Else leave blank / zero
            if manual_main_up:
                main_unit = manual_main_up
            else:
                main_unit = parsed_main or ''

            if manual_alt_up:
                alt_unit = manual_alt_up
            else:
                alt_unit = parsed_alt or ''

            if manual_qty is not None:
                alt_qty = manual_qty
            else:
                # if parser gave a positive qty, take it; else 0
                alt_qty = parsed_qty or 0

            # Extra cleaning rules (same as before)
            if '(' not in desc and not group_form:
                group = ''

            if '/' not in desc and not mrp_form_raw:
                mrp_val = 0

            # assign values
            item.description = desc
            item.item_group = group
            item.mrp = mrp_val
            item.item_size = size
            item.main_unit = main_unit
            item.alt_unit = alt_unit
            item.alt_qty = alt_qty

            # prices
            item.purc_price = round(safe_float(request.form.get('purc_price'), 0.0), 2)
            item.bulk_sp1 = round(safe_float(request.form.get('bulk_sp1'), 0.0), 2)
            item.bulk_sp2 = round(safe_float(request.form.get('bulk_sp2'), 0.0), 2)
            item.sale_price = round(safe_float(request.form.get('sale_price'), 0.0), 2)

            item.supplier = (request.form.get('supplier') or '').strip()

            # set last_updated timestamp (UTC)
            try:
                item.last_updated = datetime.utcnow()
            except Exception:
                current_app.logger.debug("Model may not have last_updated or failed to set it.")

            if not item_id:
                db.session.add(item)
            db.session.commit()
            flash('Item saved successfully!', 'success')
            return redirect(url_for('records.records'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error saving item")
            flash(f'Error saving item: {e}', 'danger')

    # GET: load item if editing
    edit_id = request.args.get('id')
    item = None
    if edit_id:
        try:
            item = Item.query.get(int(edit_id))
        except Exception:
            item = None

    return render_template('add_item.html', item=item)
