from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Show
from scheduler import refresh_schedule
from flask_migrate import Migrate
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
db.init_app(app)
migrate = Migrate(app, db)

def extract_time(time_str):
    match = re.match(r"(\d{2}:\d{2})", time_str)
    return match.group(1) if match else time_str

@app.route('/')
def index():
    """Home page with a list of shows and pagination."""
    
    page = request.args.get('page', 1, type=int)
    shows = Show.query.paginate(page=page, per_page=10)
    return render_template('index.html', shows=shows)

@app.route('/update_schedule', methods=['POST'])
def update_schedule():
    """Route to refresh the schedule."""
    
    refresh_schedule()
    return redirect(url_for('index'))

@app.route('/show/add', methods=['GET', 'POST'])
def add_show():
    """Route to add a new show to the schedule."""
    
    if request.method == 'POST':
        show = Show(
            host_first_name=request.form['host_first_name'],
            host_last_name=request.form['host_last_name'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
            days_of_week=request.form['days_of_week']
        )
        db.session.add(show)
        db.session.commit()
        flash("Show added successfully!")
        return redirect(url_for('index'))

    return render_template('add_show.html')

@app.route('/show/edit/<int:id>', methods=['GET', 'POST'])
def edit_show(id):
    """Route to edit an existing show."""
    
    show = Show.query.get_or_404(id)

    if request.method == 'POST':
        show.host_first_name = request.form['host_first_name']
        show.host_last_name = request.form['host_last_name']
        show.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        show.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        show.start_time = datetime.strptime(extract_time(request.form['start_time']), '%H:%M').time()
        show.end_time = datetime.strptime(extract_time(request.form['end_time']), '%H:%M').time()
        show.days_of_week = request.form['days_of_week']

        db.session.commit()
        flash("Show updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit_show.html', show=show)

@app.route('/show/delete/<int:id>', methods=['POST'])
def delete_show(id):
    """Route to delete a show from the schedule."""
    
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    flash("Show deleted successfully!")
    return redirect(url_for('index'))

@app.route('/clear_all', methods=['POST'])
def clear_all():
    """Route to clear all shows from the database."""
    
    db.session.query(Show).delete()
    db.session.commit()
    flash("All shows have been deleted.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
