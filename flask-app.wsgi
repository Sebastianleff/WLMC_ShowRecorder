import sys
sys.path.insert(0, '/opt/flask-app')

from app import create_app 
application = create_app()