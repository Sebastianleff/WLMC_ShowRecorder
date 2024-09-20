import ffmpeg

stream_url = 'https://wlmc.landmark.edu:8880/stream'
#stream_url = 'http://localhost:8000/stream'
duration = 100
output_file = 'stream.mp3'

def record_stream(stream_url, duration, output_file):
    try:
        (
            ffmpeg
            .input(stream_url, t=duration, **{'re': None})
            .output(output_file, acodec='copy')
            # .global_args('-loglevel', 'error')  # Suppress console output
            .overwrite_output()
            .run()
        )
        print(f"Recording saved as {output_file}")
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}")

record_stream(stream_url, duration, output_file)
