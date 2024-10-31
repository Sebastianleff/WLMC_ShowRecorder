from apscheduler.schedulers.background import BackgroundScheduler
from .models import db, Show
from config import Config
from sqlalchemy import inspect
import logging
import os
import ffmpeg
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(Config.output_folder, exist_ok=True)

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize and start the scheduler with the Flask app context."""
    scheduler.start()
    with app.app_context():
        refresh_schedule(app)

def refresh_schedule(app):
    """Refresh the scheduler with the latest shows from the database."""
    inspector = inspect(db.engine)
    if 'show' in inspector.get_table_names():
        scheduler.remove_all_jobs()
        shows = Show.query.all()
        for show in shows:
            schedule_recording(show)
        logger.info("Schedule updated successfully.")
    else:
        logger.warning("The 'show' table does not exist yet. Skipping scheduler setup.")

def record_stream(stream_url, duration, output_file):
    """Records the stream using FFmpeg."""
    try:
        logger.info(f"Starting recording: {output_file} for {duration} seconds")
        (
            ffmpeg
            .input(stream_url, t=duration)
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
    """Schedules the recording and deletion of a show."""
    now = datetime.now()
    start_time = datetime.combine(now.date(), show.start_time)
    end_time = datetime.combine(now.date(), show.end_time)
    duration = (end_time - start_time).total_seconds()
    output_file = f"{Config.output_folder}/{show.host_first_name}_{show.host_last_name}_{start_time.strftime('%Y%m%d_%H%M%S')}.mp3"

    scheduler.add_job(
        record_stream, 'date', run_date=start_time,
        args=[Config.stream_url, duration, output_file]
    )
    scheduler.add_job(
        delete_show, 'date', run_date=datetime.combine(show.end_date, show.end_time),
        args=[show.id]
    )
