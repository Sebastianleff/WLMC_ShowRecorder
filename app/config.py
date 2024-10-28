import os

stream_url = 'https://wlmc.landmark.edu:8880/stream'
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "a_secure_random_fallback_key")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    stream_url = 'https://wlmc.landmark.edu:8880/stream'
    output_folder = 'recordings'
