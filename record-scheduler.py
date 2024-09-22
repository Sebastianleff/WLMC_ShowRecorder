import os
import json
import ffmpeg
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configure logging
logging.basicConfig(
    filename='recording.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Static definitions
# STREAM_URL = 'http://localhost:8880/stream'
STREAM_URL = 'https://wlmc.landmark.edu:8880/stream'
SAVE_PATH = ''

# Function to generate filenames based on host's name
def generate_filename(host_first_name, host_last_name, timestamp):
    filename = f"{host_first_name}_{host_last_name}_{timestamp.strftime('%m_%d_%Y')}_RAWDATA.mp3"
    full_path = os.path.join(SAVE_PATH, filename)
    return full_path

# Function to record the stream
def record_stream(duration, output_file):
    try:
        logging.info(f"Starting recording: {output_file}")
        (
            ffmpeg
            .input(STREAM_URL, t=duration)
            .output(output_file, acodec='copy')
            .overwrite_output()
            .run()
        )
        logging.info(f"Recording saved as {output_file}")
    except ffmpeg.Error as e:
        logging.error(f"An error occurred: {e.stderr.decode()}")

# Load schedules from JSON
def load_schedules():
    with open('schedule.json', 'r') as f:
        return json.load(f)

# Schedule all recordings
def schedule_all_recordings():
    schedules = load_schedules()
    scheduler.remove_all_jobs()
    for show in schedules:
        if not show.get('active', True):
            continue  # Skip inactive shows
        days_of_week = show['days_of_week']
        start_time = datetime.strptime(show['start_time'], '%H:%M').time()
        duration = show['duration']
        host_first_name = show['host_first_name']
        host_last_name = show['host_last_name']
        # Generate the output filename
        # The actual timestamp will be added at runtime
        # Schedule the recording
        trigger = CronTrigger(
            day_of_week=','.join(days_of_week),
            hour=start_time.hour,
            minute=start_time.minute
        )
        scheduler.add_job(
            record_show,
            trigger=trigger,
            args=[duration, host_first_name, host_last_name],
            name=f"{host_first_name} {host_last_name}'s Show"
        )
    logging.info("Schedules have been updated.")

# Function to record the show
def record_show(duration, host_first_name, host_last_name):
    timestamp = datetime.now()
    output_file = generate_filename(host_first_name, host_last_name, timestamp)
    # Ensure the save path exists
    os.makedirs(SAVE_PATH, exist_ok=True)
    record_stream(duration, output_file)

# File system event handler for schedule.json
class ScheduleFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('schedule.json'):
            logging.info('Schedule file changed. Reloading schedules...')
            schedule_all_recordings()

if __name__ == '__main__':
    # Initialize the scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()

    # Schedule initial recordings
    schedule_all_recordings()

    # Set up file observer to watch for changes in schedule.json
    event_handler = ScheduleFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    # Keep the script running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        observer.stop()
    observer.join()
