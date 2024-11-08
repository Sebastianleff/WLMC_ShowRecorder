from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import inspect
from datetime import datetime
from .models import db, Show
from config import Config
import logging
import ffmpeg
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)

scheduler = BackgroundScheduler()

def init_scheduler(app):
	"""Initialize and start the scheduler with the Flask app context."""
	
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
	
	output_file = f"{output_file}_{datetime.now().strftime('%y-%d-%m')}_RAWDATA.mp3"

	try:
		logger.info(f"Starting recording: {output_file} for {duration} seconds")
		(
			ffmpeg
			.input(STREAM_URL, t=duration)
			.output(output_file, acodec='copy')
			.overwrite_output()
			.run()
		)
		logger.info(f"Recording saved as {output_file}")
	except ffmpeg._run.Error as e:
		logger.error(f"Recording error: {e.stderr.decode()}")
		
def delete_show(show_id):
	"""Delete a show from the database after its last airing."""
	
	with db.app_context():
		show = Show.query.get(show_id)
		if show:
			db.session.delete(show)
			db.session.commit()
			logger.info(f"Show {show_id} deleted.")

def schedule_recording(show):
	"""Schedules the recurring recording and deletion of a show."""
	
	start_time = datetime.combine(show.start_date, show.start_time)
	day_of_week = show.days_of_week
	duration = (datetime.combine(show.start_date, show.end_time) - start_time).total_seconds()
	output_file = f"{Config.OUTPUT_FOLDER}/{show.host_first_name}_{show.host_last_name}"
	delete_end_time = datetime.combine(show.end_date, show.end_time)

	scheduler.add_job(
		record_stream, 'cron',
		day_of_week=day_of_week, hour=show.start_time.hour, minute=show.start_time.minute,
		args=[Config.STREAM_URL, duration, output_file],
		start_date=start_time,
		end_date=show.end_date,
		misfire_grace_time=300,
		replace_existing=True,
		id=f"record_{show.id}"
	)

	scheduler.add_job(
		delete_show, 'date', 
		run_date=delete_end_time,
		args=[show.id],
		misfire_grace_time=600,
		replace_existing=True,
		id=f"delete_{show.id}"
	)