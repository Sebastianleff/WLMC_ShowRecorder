from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time, timedelta
from sqlalchemy import inspect
from flask import current_app
from .models import db, Show
from threading import Lock
from config import Config
import ffmpeg
import os

config_lock = Lock()
os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)

scheduler = BackgroundScheduler()

def set_pause_flag_false():
	"""Set the pause flag to False to resume recordings."""
 
	config_file = os.path.join(current_app.instance_path, 'user_config.py')
	with open(config_file, 'a') as f:
		f.write("PAUSE_SHOWS_RECORDING = False\n")
	with config_lock:
		current_app.config.from_pyfile(config_file, silent=True)

def init_scheduler(app):
	"""Initialize and start the scheduler with the Flask app context."""
 
	if not scheduler.running:
		scheduler.start()
		with app.app_context():
			current_app.logger.info("Scheduler initialized and started.")
			refresh_schedule()

def refresh_schedule():
	"""Refresh the scheduler with the latest shows from the database."""
 
	try:
		inspector = inspect(db.engine)
		'show' in inspector.get_table_names()
		scheduler.remove_all_jobs()
		shows = Show.query.all()
		for show in shows:
			schedule_recording(show)
		current_app.logger.info("Schedule refreshed with latest shows.")
	except Exception as e:
		current_app.logger.error(f"Error refreshing schedule: {e}")

def pause_shows_until(date):
	"""Pause all recordings until a specified date."""
 
	try:
		scheduler.add_job(
			set_pause_flag_false, 'date',
			run_date=date
		)
		current_app.logger.info(f"Recordings resume job added.")
	except Exception as e:
		current_app.logger.error(f"Error adding resume jobs: {e}")

def record_stream(STREAM_URL, duration, output_file):
	"""Records the stream using FFmpeg."""

	if current_app.config['PAUSE_SHOWS_RECORDING'] is True:
		current_app.logger.info("Recordings paused.")
		return

	output_file = f"{output_file}_{datetime.now().strftime('%m-%d-%y')}_RAWDATA.mp3"
	start_time = datetime.now().strftime('%H-%M-%S')
	try:
		(
			ffmpeg
			.input(STREAM_URL, t=duration)
			.output(output_file, acodec='copy')
			.overwrite_output()
			.run()
		)
		current_app.logger.info(f"Recording started for {output_file}.")
		current_app.logger.info(f"Start time:{start_time}.")
	except ffmpeg.Error as e:
		current_app.logger.error(f"FFmpeg error: {e.stderr.decode()}")

def delete_show(show_id):
	"""Delete a show from the database after its last airing."""
 
	try:
		with db.app_context():
			show = Show.query.get(show_id)
			if show:
				db.session.delete(show)
				db.session.commit()
		current_app.logger.info(f"Show with ID {show_id} deleted after last airing.")
		refresh_schedule()
	except Exception as e:
		current_app.logger.error(f"Error deleting show {show_id}: {e}")

def schedule_recording(show):
	"""Schedules the recurring recording and deletion of a show."""
	
	start_time = datetime.combine(show.start_date, show.start_time)
	end_time = datetime.combine(show.start_date, show.end_time)
	
	if show.end_time == time(0, 0):
		end_time += timedelta(days=1)
	
	duration = (end_time - start_time).total_seconds()
	stream_url = current_app.config['STREAM_URL']
	
	if current_app.config['AUTO_CREATE_SHOW_FOLDERS']:
		show_folder = os.path.join(current_app.config['OUTPUT_FOLDER'], f"{show.host_first_name} {show.host_last_name}")
		if not os.path.exists(show_folder):
			os.mkdir(show_folder)
	else:
		show_folder = current_app.config['OUTPUT_FOLDER']
	
	output_file = os.path.join(show_folder, f"{show.host_first_name}_{show.host_last_name}")

	try:
		scheduler.add_job(
			record_stream, 'cron',
			day_of_week=show.days_of_week, hour=show.start_time.hour, minute=show.start_time.minute,
			args=[stream_url, duration, output_file],
			start_date=start_time,
			end_date=show.end_date,
		)
		current_app.logger.info(f"Recording scheduled for show {show.id}.")

		scheduler.add_job(
			delete_show, 'date',
			run_date=show.end_date + timedelta(days=1),
			args=[show.id]
		)
		current_app.logger.info(f"Deletion scheduled for show {show.id} after last airing.")
	except Exception as e:
		current_app.logger.error(f"Error scheduling recording for show {show.id}: {e}")

