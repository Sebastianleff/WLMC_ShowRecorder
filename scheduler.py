from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Show
from config import Config
from datetime import datetime
import ffmpeg
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(Config.output_folder, exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

scheduler = BackgroundScheduler()
scheduler.start()

def delete_show(show_id):
    """Deletes a show from the database by its ID after the last airing."""
    with app.app_context():
        show = Show.query.get(show_id)
        if show:
            db.session.delete(show)
            db.session.commit()
            logger.info(f"Show {show_id} has been deleted after its final episode.")
            
def record_stream(stream_url, duration, output_file):
    """Records audio from a stream URL using FFmpeg."""
    
    try:
        logger.info(f"Starting recording: {output_file} for {duration} seconds")
        (
            ffmpeg
            .input(stream_url, t=duration, **{'re': None})
            .output(output_file, acodec='copy')
            .overwrite_output()
            .run()
        )
        logger.info(f"Recording saved as {output_file}")
    except ffmpeg._run.Error as e:
        logger.error(f"An error occurred during recording: {e.stderr.decode()}")

def schedule_recording(show):
    """Schedules a recording for a specific show and its deletion after the last episode."""
    
    logger.info(f"Scheduling recording for show: {show.host_first_name} {show.host_last_name} at {show.start_time}")
    
    now = datetime.now()
    start_time = datetime.combine(now.date(), show.start_time)
    end_time = datetime.combine(now.date(), show.end_time)
    last_airing = datetime.combine(show.end_date, show.end_time)
    duration = int((end_time - start_time).total_seconds())

    output_file = f"{Config.output_folder}/{show.host_first_name}_{show.host_last_name}_{start_time.strftime('%m_%d_%Y')}_RAWDATA.mp3"

    scheduler.add_job(
        record_stream,
        'date',
        run_date=start_time,
        args=[Config.stream_url, duration, output_file],
        id=f"record_{show.id}_{start_time.strftime('%Y%m%d_%H%M%S')}"
    )
    
    scheduler.add_job(
        delete_show,
        'date',
        run_date=last_airing,
        args=[show.id],
        id=f"delete_{show.id}"
    )
    

def refresh_schedule():
    """Clears existing schedule and loads new show times from the database."""
    
    scheduler.remove_all_jobs()
    
    with app.app_context():
        shows = Show.query.all()
        for show in shows:
            schedule_recording(show)
            
    logger.info("Schedule updated successfully.")
