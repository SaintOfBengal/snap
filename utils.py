import os
import subprocess

MAX_SIZE = 50 * 1024 * 1024  # 50 MB

def format_duration(seconds):
    """
    Formats a duration in seconds into a HH:MM:SS or MM:SS string.
    """
    try:
        secs = int(seconds)
        hrs, rem = divmod(secs, 3600)
        mins, secs = divmod(rem, 60)
        if hrs > 0:
            return f"{int(hrs):02d}:{int(mins):02d}:{int(secs):02d}"
        else:
            return f"{int(mins):02d}:{int(secs):02d}"
    except (TypeError, ValueError):
        return "N/A"

def compress_video_to_target_size(input_path, output_path, duration_seconds):
    """
    Compresses a video to a target size by calculating the required bitrate.
    """
    target_size_mb = 48
    target_size_bits = target_size_mb * 1024 * 1024 * 8

    try:
        duration_seconds = int(duration_seconds)
        if duration_seconds <= 0:
            duration_seconds = 1
    except (TypeError, ValueError):
        duration_seconds = 1
        
    total_bitrate = target_size_bits / duration_seconds
    audio_bitrate_bits = 128 * 1000
    video_bitrate_bits = total_bitrate - audio_bitrate_bits

    # Ensure video bitrate isn't too low and adjust audio if necessary
    if video_bitrate_bits < 100 * 1000:
        video_bitrate_bits = 100 * 1000
        audio_bitrate_bits = 64 * 1000

    video_bitrate_k = int(video_bitrate_bits / 1000)
    audio_bitrate_k = int(audio_bitrate_bits / 1000)

    # FFmpeg command to compress the video
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-b:v", f"{video_bitrate_k}k",
        "-c:a", "aac", "-b:a", f"{audio_bitrate_k}k",
        "-preset", "fast", # 'ultrafast' is faster but lower quality, 'fast' is a good balance
        "-v", "error", # Only show errors in the console
        output_path
    ]
    subprocess.run(cmd, check=True)

def cleanup_files(*paths):
    """
    Deletes one or more files and ignores any errors if the file doesn't exist.
    """
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            # This will catch errors like permission issues
            pass