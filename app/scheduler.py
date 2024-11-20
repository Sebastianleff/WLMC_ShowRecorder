from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from sqlalchemy import inspect
from datetime import datetime, time, timedelta
from .models import db, Show
from config import Config
import ffmpeg
import os

os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)

scheduler = BackgroundScheduler()

def init_scheduler(app):
	"""Initialize and start the scheduler with the Flask app context."""
 
	if not scheduler.running:
		scheduler.start()
		with app.app_context():
			refresh_schedule()

def refresh_schedule():
	"""Refresh the scheduler with the latest shows from the database."""
 
	inspector = inspect(db.engine)
	'show' in inspector.get_table_names()
	scheduler.remove_all_jobs()
	shows = Show.query.all()
	for show in shows:
		schedule_recording(show)

def record_stream(STREAM_URL, duration, output_file):
	"""Records the stream using FFmpeg."""
	output_file = f"{output_file}_{datetime.now().strftime('%m-%d-%y')}_RAWDATA.mp3"
	try:
		(
			ffmpeg
			.input(STREAM_URL, t=duration)
			.output(output_file, acodec='copy')
			.overwrite_output()
			.run()
		)
	except ffmpeg._run.Error as e:
		current_app.logger.error(f"FFmpeg error: {e.stderr.decode()}")

def delete_show(show_id):
	"""Delete a show from the database after its last airing."""
 
	with db.app_context():
		show = Show.query.get(show_id)
		if show:
			db.session.delete(show)
			db.session.commit()
	refresh_schedule()

def schedule_recording(show):
	"""Schedules the recurring recording and deletion of a show."""
	
	if isinstance(show.start_time, int):
		show.start_time = time(hour=show.start_time // 100, minute=show.start_time % 100)
	if isinstance(show.end_time, int):
		show.end_time = time(hour=show.end_time // 100, minute=show.end_time % 100)
	
	start_time = datetime.combine(show.start_date, show.start_time)
	end_time = datetime.combine(show.start_date, show.end_time)
	
	if show.end_time == time(0, 0):
		end_time += timedelta(days=1)
	
	duration = (end_time - start_time).total_seconds()
	stream_url = current_app.config['STREAM_URL']
	
	if current_app.config['AUTO_CREATE_SHOW_FOLDERS']:
		show_folder = os.path.join(current_app.config['OUTPUT_FOLDER'], f"{show.host_first_name}_{show.host_last_name}")
		if not os.path.exists(show_folder):
			os.mkdir(show_folder)
	else:
		show_folder = current_app.config['OUTPUT_FOLDER']
	
	output_file = os.path.join(show_folder, f"{show.host_first_name}_{show.host_last_name}")

	scheduler.add_job(
		record_stream, 'cron',
		day_of_week=show.days_of_week, hour=show.start_time.hour, minute=show.start_time.minute,
		args=[stream_url, duration, output_file],
		start_date=start_time,
		end_date=show.end_date,
	)
 
	scheduler.add_job(
		delete_show, 'date',
		run_date=show.end_date + timedelta(days=1),
		args=[show.id]
	)