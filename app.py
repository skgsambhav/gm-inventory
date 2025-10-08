# app.py
import os
import logging
from flask import Flask, jsonify
from extensions import db
from config import config

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Load configuration
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)

    # Configure logging
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

    # Import models
    import models  # noqa: F401

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes.add_item import add_item_bp
    from routes.records import records_bp

    app.register_blueprint(add_item_bp)
    app.register_blueprint(records_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if app.config.get('DEBUG'):
            return str(error), 404
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        if app.config.get('DEBUG'):
            return str(error), 500
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({
            'success': False,
            'message': 'File too large. Maximum size is 16MB.'
        }), 413

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
