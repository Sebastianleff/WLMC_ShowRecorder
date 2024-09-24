import os
import json
import ffmpeg
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Static definitions
STREAM_URL = 'http://localhost:8000/stream'
STATION_NAME = 'WLMC Landmark College Radio'
SAVE_PATH = '/path/to/local/recordings/'

# Function to generate filenames based on host's name
def generate_filename(host_first_name, host_last_name, timestamp):
    filename = f"{STATION_NAME}_{host_first_name}_{host_last_name}_{timestamp.strftime('%m_%d_%Y')}_RAWDATA.mp3"
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

