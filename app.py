import sys
print("Python path:", sys.executable)
print("Python version:", sys.version)

import os
import logging
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
migrate = Migrate(app, db) 

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-secret-key-here")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Root route
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Import routes after app initialization
with app.app_context():
    try:
        # Import models first
        from models import User, Class, Student, Attendance
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully!")

        # Import and register blueprints
        from auth import auth_bp
        from attendance import attendance_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(attendance_bp)

    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))