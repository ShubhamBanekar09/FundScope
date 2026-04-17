from flask import Flask
from config import Config
from app.dbconfig.extensions import db  # Import the database instance

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize the database with the app
    db.init_app(app)
    
    # Automatically create the SQLite database file and tables if they don't exist
    try:
        with app.app_context():
            from app.dbconfig import models
            db.create_all()
            print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        # Continue anyway - tables may already exist

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.ai import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)

    return app