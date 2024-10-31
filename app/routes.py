from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .models import db, Show
from .scheduler import refresh_schedule
from functools import wraps
from datetime import datetime
import re

main_bp = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route for admin authentication."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == current_app.config['ADMIN_USERNAME'] and
                password == current_app.config['ADMIN_PASSWORD']):
            session['authenticated'] = True
            flash("You are now logged in.", "success")
            return redirect(url_for('main.index'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    """Logout route to clear the session."""
    session.pop('authenticated', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('main.login'))

@main_bp.route('/')
@admin_required
def index():
    """Render the home page with paginated shows."""
    page = request.args.get('page', 1, type=int)
    shows = Show.query.paginate(page=page, per_page=10)
    return render_template('index.html', shows=shows)

@main_bp.route('/update_schedule', methods=['POST'])
@admin_required
def update_schedule():
    """Route to refresh the schedule."""
    refresh_schedule(current_app)
    flash("Schedule updated successfully!", "info")
    return redirect(url_for('main.index'))

@main_bp.route('/show/add', methods=['GET', 'POST'])
@admin_required
def add_show():
    """Route to add a new show."""
    if request.method == 'POST':
        try:
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
            flash("Show added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        return redirect(url_for('main.index'))

    return render_template('add_show.html')

@main_bp.route('/show/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_show(id):
    """Route to edit an existing show."""
    show = Show.query.get_or_404(id)
    if request.method == 'POST':
        try:
            show.host_first_name = request.form['host_first_name']
            show.host_last_name = request.form['host_last_name']
            show.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            show.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            show.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            show.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            show.days_of_week = request.form['days_of_week']

            db.session.commit()
            flash("Show updated successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
        return redirect(url_for('main.index'))

    return render_template('edit_show.html', show=show)

@main_bp.route('/show/delete/<int:id>', methods=['POST'])
@admin_required
def delete_show(id):
    """Route to delete a show."""
    show = Show.query.get_or_404(id)
    db.session.delete(show)
    db.session.commit()
    flash("Show deleted successfully!", "success")
    return redirect(url_for('main.index'))

@main_bp.route('/clear_all', methods=['POST'])
@admin_required
def clear_all():
    """Route to clear all shows."""
    db.session.query(Show).delete()
    db.session.commit()
    flash("All shows have been deleted.", "info")
    return redirect(url_for('main.index'))
