from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from .scheduler import refresh_schedule
from datetime import datetime
from .models import db, Show
from functools import wraps
import logging
import os

logging.basicConfig(level=logging.DEBUG)

main_bp = Blueprint('main', __name__)

def admin_required(f):
	"""Decorator to require admin authentication."""
 
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not session.get('authenticated'):
			flash("Please log in to access this page.", "danger")
			return redirect(url_for('main.login'))
		return f(*args, **kwargs)
	return decorated_function

@main_bp.route('/')
def index():
	"""Redirect to the shows page."""
	
	return redirect(url_for('main.shows'))

@main_bp.route('/shows')
@admin_required
def shows():
	"""Render the shows database page with paginated shows."""
	
	page = request.args.get('page', 1, type=int)
	shows = Show.query.paginate(page=page, per_page=15)
	return render_template('shows_database.html', shows=shows)

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
			return redirect(url_for('main.shows'))
		else:
			flash("Invalid credentials. Please try again.", "danger")
	return render_template('login.html')

@main_bp.route('/logout')
def logout():
	"""Logout route to clear the session."""
 
	try:
		session.pop('authenticated', None)
		#flash("You are now logged out.", "info") removed becouse of index display issue
		return redirect(url_for('main.index'))
	except Exception as e:
		flash(f"Error logging out: {e}", "danger")
		return redirect(url_for('main.shows'))

@main_bp.route('/show/add', methods=['GET', 'POST'])
@admin_required
def add_show():
	"""Route to add a new show."""
	
	try:
		if request.method == 'POST':
			start_date = request.form['start_date'] or current_app.config['DEFAULT_START_DATE']
			end_date = request.form['end_date'] or current_app.config['DEFAULT_END_DATE']
			start_time = request.form['start_time']
			end_time = request.form['end_time']

			start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
			end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
			start_time_obj = datetime.strptime(start_time, '%H:%M').time()
			end_time_obj = datetime.strptime(end_time, '%H:%M').time()

			today = datetime.today().date()
			if end_date_obj < today:
				flash("End date cannot be in the past!", "danger")
				return redirect(url_for('main.add_show'))

			if end_time_obj == datetime.time(0, 0) and start_time_obj != datetime.time(0, 0):
				pass
			elif end_time_obj <= start_time_obj:
				flash("End time cannot be before start time!", "danger")
				return redirect(url_for('main.add_show'))

			short_day_name = request.form['days_of_week'].lower()[:3]
			
			show = Show(
				host_first_name=request.form['host_first_name'],
				host_last_name=request.form['host_last_name'],
				start_date=start_date_obj,
				end_date=end_date_obj,
				start_time=start_time_obj,
				end_time=end_time_obj,
				days_of_week=short_day_name
			)
			db.session.add(show)
			db.session.commit()
			update_schedule()
			flash("Show added successfully!", "success")
			return redirect(url_for('main.shows'))
		
		return render_template('add_show.html')
	except Exception as e:
		flash(f"Error adding show: {e}", "danger")
		return redirect(url_for('main.shows'))

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

			return redirect(url_for('main.shows'))

		return render_template('edit_show.html', show=show)
	except Exception as e:
		flash(f"Error editing show: {e}", "danger")
		return redirect(url_for('main.shows'))

@main_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
	"""Route to update the application settings."""
	
	config_file = os.path.join(current_app.instance_path, 'user_config.py')

	if request.method == 'POST':
		try:
			settings = {
				'ADMIN_USERNAME': request.form['admin_username'],
				'ADMIN_PASSWORD': request.form['admin_password'],
				'STREAM_URL': request.form['stream_url'],
				'OUTPUT_FOLDER': request.form['output_folder'],
				'DEFAULT_START_DATE': request.form['default_start_date'],
				'DEFAULT_END_DATE': request.form['default_end_date'],
				'AUTO_CREATE_SHOW_FOLDERS': 'auto_create_show_folders' in request.form,
			}

			with open(config_file, 'w') as f:
				for key, value in settings.items():
						f.write(f"{key} = {repr(value)}\n")

			flash("Settings updated successfully!", "success")
			return redirect(url_for('main.shows'))
			
		except Exception as e:
			flash(f"An error occurred while updating settings: {str(e)}", "danger")
			return redirect(url_for('main.settings'))

	config = current_app.config
	settings_data = {
		'admin_username': config.get("ADMIN_USERNAME"),
		'admin_password': config.get("ADMIN_PASSWORD"),
		'stream_url': config.get("STREAM_URL"),
		'output_folder': config.get("OUTPUT_FOLDER"),
		'default_start_date': config.get("DEFAULT_START_DATE"),
		'default_end_date': config.get("DEFAULT_END_DATE"),
		'auto_create_show_folders': config.get("AUTO_CREATE_SHOW_FOLDERS"),
	}
	
	return render_template('settings.html', **settings_data)

@main_bp.route('/update_schedule', methods=['POST'])
@admin_required
def update_schedule():
	"""Route to refresh the schedule."""
 
	try:
		refresh_schedule()
		flash("Schedule updated successfully!", "success")
		return redirect(url_for('main.shows'))
	except Exception as e:
		flash(f"Error updating schedule: {e}", "danger")
		return redirect(url_for('main.shows'))

@main_bp.route('/show/delete/<int:id>', methods=['POST'])
@admin_required
def delete_show(id):
	"""Route to delete a show."""
 
	try:
		show = Show.query.get_or_404(id)
		db.session.delete(show)
		db.session.commit()
		flash("Show deleted successfully!", "success")
		return redirect(url_for('main.shows'))
	except Exception as e:
		flash(f"Error deleting show: {e}", "danger")
		return redirect(url_for('main.shows'))

@main_bp.route('/clear_all', methods=['POST'])
@admin_required
def clear_all():
	"""Route to clear all shows."""
 
	try:
		db.session.query(Show).delete()
		db.session.commit()
		flash("All shows have been deleted.", "info")
		return redirect(url_for('main.shows'))
	except Exception as e:
		flash(f"Error deleting shows: {e}", "danger")
		return redirect(url_for('main.shows'))