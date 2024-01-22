import os
import random
import datetime
import subprocess
import re
import sys


def get_video_duration(episode_path):
    """Get the duration of a video using ffmpeg."""

    # Run the ffmpeg command and capture its output
    try:
        result = subprocess.run(["ffmpeg", "-i", episode_path], stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        return "FFmpeg is not installed or not found in the system path."

    # Extract the duration using regular expression
    duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", result.stderr)
    if duration_match:
        return duration_match.group(1)
    else:
        return "Duration not found."


def parse_duration(duration_str):
    """Converts duration from HH:MM:SS to seconds."""
    time_parts = duration_str.split(':')
    hours, minutes, seconds = int(time_parts[0]), int(time_parts[1]), float(time_parts[2])
    return hours * 3600 + minutes * 60 + int(seconds)

def seconds_to_hms(seconds):
    """Converts seconds to HH:MM:SS format."""
    return str(datetime.timedelta(seconds=seconds))


def get_start_and_end(episode_length):
    total_duration_seconds = parse_duration(episode_length)
    random_start_seconds = random.randint(0, total_duration_seconds)
    # end_time_seconds = min(random_start_seconds + 60, total_duration_seconds)
    start_time = seconds_to_hms(random_start_seconds)
    # end_time = seconds_to_hms(end_time_seconds)
    return start_time

def extract_frames(episode_path, duration, fps, output_dir):
    """Extract frames from a video file."""
    episode_length = get_video_duration(episode_path)
    start_time = get_start_and_end(episode_length)
    
    # clear output directory
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(['rm', '-rf', f'{output_dir}/*'])
    output_path = f'{output_dir}/%04d.png'
    subprocess.run(['ffmpeg', '-i', episode_path, '-vf', f'fps={fps}', '-ss', start_time, '-t', duration, output_path])
    print(f'Extracted frames from {episode_path} starting at {start_time} for {duration} at {fps} fps')


episode_path = sys.argv[1]
duration = sys.argv[2]
fps = sys.argv[3]
output_dir = sys.argv[4]
extract_frames(episode_path, duration, fps, output_dir)