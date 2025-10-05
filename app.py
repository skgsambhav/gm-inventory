# app.py
import os
from flask import Flask
from extensions import db  # single, shared SQLAlchemy instance
# Do NOT import routes at module-level here — import after db.init_app

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get("FLASK_SECRET", "supersecretkey")

    # Initialize DB with app
    db.init_app(app)

    # Import models so SQLAlchemy knows about them (safe after init_app)
    # import models here to ensure model classes are registered with this db
    import models  # noqa: F401

    # Create DB tables if they don't exist
    with app.app_context():
        db.create_all()

    # Now import and register blueprints (after db is initialized)
    from routes.add_item import add_item_bp
    from routes.records import records_bp

    app.register_blueprint(add_item_bp)
    app.register_blueprint(records_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
