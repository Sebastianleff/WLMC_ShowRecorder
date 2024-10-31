import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "a_not_so_secure_fallback_key")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    stream_url = 'https://wlmc.landmark.edu:8880/stream'
    output_folder = 'recordings'
