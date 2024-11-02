import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .models import db, Show
from .scheduler import refresh_schedule
from functools import wraps
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

main_bp = Blueprint('main', __name__)

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not session.get('authenticated'):
			flash("Please log in to access this page.", "danger")
			return redirect(url_for('main.login'))
		return f(*args, **kwargs)
	return decorated_function

@main_bp.route('/')
@admin_required
def index():
	"""Render the home page with paginated shows."""
 
	page = request.args.get('page', 1, type=int)
	shows = Show.query.paginate(page=page, per_page=10)
	return render_template('index.html', shows=shows)

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
	try:
		session.pop('authenticated', None)
		flash("You have been logged out.", "info")
		return redirect(url_for('main.login'))
	except Exception as e:
		flash(f"Error logging out: {e}", "danger")
		return redirect(url_for('main.index'))

@main_bp.route('/update_schedule', methods=['POST'])
@admin_required
def update_schedule():
	"""Route to refresh the schedule."""
 
	try:
		refresh_schedule()
		flash("Schedule updated successfully!", "success")
		return redirect(url_for('main.index'))
	except Exception as e:
		flash(f"Error updating schedule: {e}", "danger")
		return redirect(url_for('main.index'))

@main_bp.route('/show/add', methods=['GET', 'POST'])
@admin_required
def add_show():
	"""Route to add a new show."""
 
	try:
		if request.method == 'POST':
			short_day_name = request.form['days_of_week'].lower()[:3]
			show = Show(
				host_first_name=request.form['host_first_name'],
				host_last_name=request.form['host_last_name'],
				start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
				end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
				start_time=datetime.strptime(request.form['start_time'], '%H:%M').time(),
				end_time=datetime.strptime(request.form['end_time'], '%H:%M').time(),
				days_of_week=short_day_name
			)
			db.session.add(show)
			db.session.commit()
			flash("Show added successfully!", "success")
	
			return redirect(url_for('main.index'))

		return render_template('add_show.html')
	except Exception as e:
		flash(f"Error adding show: {e}", "danger")
		return redirect(url_for('main.index'))

@main_bp.route('/show/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_show(id):
	"""Route to edit an existing show."""
 
	show = Show.query.get_or_404(id)
	try:
		if request.method == 'POST':
			short_day_name = request.form['days_of_week'].lower()[:3]
	
			show.host_first_name = request.form['host_first_name']
			show.host_last_name = request.form['host_last_name']
			show.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
			show.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
			show.start_time = datetime.strptime(request.form['start_time'].strip(), '%H:%M').time()
			show.end_time = datetime.strptime(request.form['end_time'].strip(), '%H:%M').time()
			show.days_of_week = short_day_name
	
			db.session.commit()
			update_schedule()
			flash("Show updated successfully!", "success")

			return redirect(url_for('main.index'))

		return render_template('edit_show.html', show=show)
	except Exception as e:
		flash(f"Error editing show: {e}", "danger")
		return redirect(url_for('main.index'))


@main_bp.route('/show/delete/<int:id>', methods=['POST'])
@admin_required
def delete_show(id):
	"""Route to delete a show."""
	try:
		show = Show.query.get_or_404(id)
		db.session.delete(show)
		db.session.commit()
		flash("Show deleted successfully!", "success")
		return redirect(url_for('main.index'))
	except Exception as e:
		flash(f"Error deleting show: {e}", "danger")
		return redirect(url_for('main.index'))

@main_bp.route('/clear_all', methods=['POST'])
@admin_required
def clear_all():
	"""Route to clear all shows."""
	try:
		db.session.query(Show).delete()
		db.session.commit()
		flash("All shows have been deleted.", "info")
		return redirect(url_for('main.index'))
	except Exception as e:
		flash(f"Error deleting shows: {e}", "danger")
		return redirect(url_for('main.index'))
