import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "a_not_so_secure_fallback_key")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STREAM_URL = os.getenv("STREAM_URL", "https://wlmc.landmark.edu:8880/stream")
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", os.path.join(os.path.abspath(os.path.dirname(__file__)), 'recordings'))
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    
