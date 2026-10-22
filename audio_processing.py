# audio_processing.py

import numpy as np

# Audio processing
import librosa
import librosa.display

# Image processing
import matplotlib.pyplot as plt
from PIL import Image

# File handling
import os
from io import BytesIO
from pathlib import Path

# Caching
from functools import lru_cache

import gradio as gr

#                       Cache functions
# ============================================================
@lru_cache(maxsize=128)
def load_audio_files_from_folder(folder_path):
    return list_audio_files_from_folder(folder_path)

@lru_cache(maxsize=128)
def load_audio(file_path):
    return file_path

@lru_cache(maxsize=128)
def get_mel_spectrogram(file_path):
    audio_data = load_audio(file_path)
    mel_spectrogram = audio_to_mel_spectrogram(audio_data)
    return mel_spectrogram

def audio_to_mel_spectrogram(audio_clip):
    """
    Convert an audio clip to a mel spectrogram image.

    Parameters:
    audio_clip (str): The path to the audio clip file.

    Returns:
    PIL.Image.Image: The mel spectrogram image.
    """
    y, sr = librosa.load(audio_clip, sr=None, mono=True)
    if y.size == 0:
        raise ValueError(f"Audio file is empty: {audio_clip}")
    # A mel spectrogram is both cheaper to render and more useful for comparing
    # tonal audio than plotting the linear-frequency STFT on a log axis.
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    try:
        librosa.display.specshow(mel_db, sr=sr, x_axis="time", y_axis="mel", ax=ax)
        ax.set(title="Mel spectrogram", xlabel="Time", ylabel="Frequency")
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        buf.seek(0)
        with Image.open(buf) as image:
            return image.copy()
    finally:
        plt.close(fig)

def list_audio_files_from_folder(folder_path):
    """
    Lists all audio files (with extensions .mp3, .wav, .WAV, .MP3) in the given folder and its subfolders.

    Args:
        folder_path (str): The path to the folder to search for audio files.

    Returns:
        list: A list of full paths to the audio files found.
    """

    folder = Path(folder_path)
    if not folder.is_dir():
        return []
    return sorted(
        (str(file) for file in folder.rglob('*') if file.is_file() and file.suffix.lower() in {'.mp3', '.wav'}),
        key=str.casefold,
    )

def extract_time_from_filename(filename):
    try:
        # Extract the 2nd and 3rd parameters from the filename
        parts = os.path.basename(filename).split("_")
        
        # Convert parts[2] (HHMMSS) to total seconds
        hhmmss = parts[2]
        hours = int(hhmmss[:2])
        minutes = int(hhmmss[2:4])
        seconds = int(hhmmss[4:6])
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        # Add the seconds from parts[3] (which is in milliseconds)
        additional_seconds = int(parts[3]) / 1000
        total_seconds += additional_seconds
        
        # Convert total seconds to HH:MM:SS format
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        # Format the result as HH:MM:SS
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except (IndexError, ValueError, TypeError):
        return "Unknown Time"

def extract_date_from_filename(filename):
    """
    Extract the date from the filename.

    Parameters:
    filename (str): The name of the file.

    Returns:
    str: The extracted date in YYYY-MM-DD format.
    """
    try:
        date_str = os.path.basename(filename).split('_')[1]  # date is second token
        if len(date_str) != 8 or not date_str.isdigit():
            return "Unknown Date"
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"  # Convert to YYYY-MM-DD format
        return date_formatted
    except IndexError:
        return "Unknown Date"

def update_audio_and_image(audio_path):
    audio = load_audio(audio_path)
    image = get_mel_spectrogram(audio_path)

    return audio, image
