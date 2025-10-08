from datetime import datetime
from extensions import db
from sqlalchemy import CheckConstraint


class Item(db.Model):
    """Item model with validation and constraints"""
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False, index=True)
    item_group = db.Column(db.String(100), nullable=True, index=True)
    mrp = db.Column(db.Integer, nullable=True)
    item_size = db.Column(db.String(100), nullable=True)
    main_unit = db.Column(db.String(50), nullable=True)
    alt_unit = db.Column(db.String(50), nullable=True)
    alt_qty = db.Column(db.Integer, nullable=True, default=0)
    purc_price = db.Column(db.Float, nullable=True, default=0.0)
    bulk_sp1 = db.Column(db.Float, nullable=True, default=0.0)
    bulk_sp2 = db.Column(db.Float, nullable=True, default=0.0)
    sale_price = db.Column(db.Float, nullable=True, default=0.0)
    supplier = db.Column(db.String(200), nullable=True, index=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Add constraints for data integrity
    __table_args__ = (
        CheckConstraint('mrp >= 0', name='check_mrp_positive'),
        CheckConstraint('purc_price >= 0', name='check_purc_price_positive'),
        CheckConstraint('bulk_sp1 >= 0', name='check_bulk_sp1_positive'),
        CheckConstraint('bulk_sp2 >= 0', name='check_bulk_sp2_positive'),
        CheckConstraint('sale_price >= 0', name='check_sale_price_positive'),
        CheckConstraint('alt_qty >= 0', name='check_alt_qty_positive'),
    )

    def __repr__(self):
        return f'<Item {self.id}: {self.description[:30]}>'

    def to_dict(self):
        """Convert item to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'description': self.description,
            'item_group': self.item_group,
            'mrp': self.mrp,
            'item_size': self.item_size,
            'main_unit': self.main_unit,
            'alt_unit': self.alt_unit,
            'alt_qty': self.alt_qty,
            'purc_price': self.purc_price,
            'bulk_sp1': self.bulk_sp1,
            'bulk_sp2': self.bulk_sp2,
            'sale_price': self.sale_price,
            'supplier': self.supplier,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    @property
    def margin_bsp1(self):
        """Calculate margin percentage for bulk_sp1"""
        if self.purc_price and self.purc_price > 0 and self.bulk_sp1:
            return round(((self.bulk_sp1 - self.purc_price) / self.purc_price) * 100, 2)
        return 0

    @property
    def margin_bsp2(self):
        """Calculate margin percentage for bulk_sp2"""
        if self.purc_price and self.purc_price > 0 and self.bulk_sp2:
            return round(((self.bulk_sp2 - self.purc_price) / self.purc_price) * 100, 2)
        return 0

    @property
    def margin_sale(self):
        """Calculate margin percentage for sale_price"""
        if self.purc_price and self.purc_price > 0 and self.sale_price:
            return round(((self.sale_price - self.purc_price) / self.purc_price) * 100, 2)
        return 0

    def validate(self):
        """Validate item data"""
        errors = []

        if not self.description or not self.description.strip():
            errors.append('Description is required')

        if self.mrp is not None and self.mrp < 0:
            errors.append('MRP must be positive')

        if self.purc_price is not None and self.purc_price < 0:
            errors.append('Purchase price must be positive')

        if self.bulk_sp1 is not None and self.bulk_sp1 < 0:
            errors.append('Bulk SP1 must be positive')

        if self.bulk_sp2 is not None and self.bulk_sp2 < 0:
            errors.append('Bulk SP2 must be positive')

        if self.sale_price is not None and self.sale_price < 0:
            errors.append('Sale price must be positive')

        if self.alt_qty is not None and self.alt_qty < 0:
            errors.append('Alt quantity must be positive')

        return errors
