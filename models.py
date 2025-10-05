from datetime import datetime
from extensions import db

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=True)
    item_group = db.Column(db.String, nullable=True)
    mrp = db.Column(db.Integer, nullable=True)
    item_size = db.Column(db.String, nullable=True)
    main_unit = db.Column(db.String, nullable=True)
    alt_unit = db.Column(db.String, nullable=True)
    alt_qty = db.Column(db.Integer, nullable=True, default=0)
    purc_price = db.Column(db.Float, nullable=True, default=0.0)
    bulk_sp1 = db.Column(db.Float, nullable=True, default=0.0)
    bulk_sp2 = db.Column(db.Float, nullable=True, default=0.0)
    sale_price = db.Column(db.Float, nullable=True, default=0.0)
    supplier = db.Column(db.String, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # ... add to_dict() if you like
