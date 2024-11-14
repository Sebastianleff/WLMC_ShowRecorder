import os

class Config:
    SECRET_KEY = "a_not_so_secure_fallback_key"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STREAM_URL = "https://wlmc.landmark.edu:8880/stream"
    OUTPUT_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "recordings")
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
