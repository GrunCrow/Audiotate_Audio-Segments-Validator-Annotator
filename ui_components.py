# ui_components.py

import os
from gradio import Blocks, Markdown, SelectData, Row, HTML
import requests
import pandas as pd
from packaging.version import InvalidVersion, Version

from audio_processing import list_audio_files_from_folder

# Caching
from functools import lru_cache

from config import CURRENT_VERSION, GITHUB_REPO
from audio_processing import update_audio_and_image, extract_date_from_filename, extract_time_from_filename

# Global variables
from config import Globals

def on_audio_selected(audio_table, evt: SelectData):
    """
    Process the selected audio and return relevant information.

    Args:
        selected_row (pandas.DataFrame): The selected row containing audio information.
        evt (gr.SelectData): The event object containing additional information.

    Returns:
        tuple: A tuple containing the following information:
            - mel_spectrogram_image (numpy.ndarray): The mel spectrogram image of the selected audio.
            - audio_path (str): The path of the selected audio file.
            - species_name (str): The name of the species associated with the selected audio.
            - selected_row_index (int): The index of the selected row.
            - sample_audio (str): The path of a sample audio file for the selected species.
            - sample_image (numpy.ndarray): The mel spectrogram image of the sample audio file.
            - suggested_specie (str): The suggested species for the selected audio.

            If no audio is selected or an error occurs, the tuple will contain None values.
    """

    if not audio_table.empty:
        if evt and evt.index:
            selected_row_index = evt.index[0]
            Globals.set_current_row_index(selected_row_index)
            audio_path = audio_table.iloc[selected_row_index]["Path"]
            audio_path = os.path.normpath(audio_path)
            time = extract_time_from_filename(audio_path)
            date = extract_date_from_filename(audio_path)
            species_name = audio_table.iloc[selected_row_index]["Specie"]
            Globals.set_current_specie_name(species_name)
            suggested_specie = audio_table.iloc[selected_row_index]["Suggested Specie"] if "Suggested Specie" in audio_table else None
            comment = audio_table.iloc[selected_row_index]["Comment"] if "Comment" in audio_table else None
            if pd.isna(suggested_specie):
                suggested_specie = None
            if pd.isna(comment):
                comment = "No Comments"
            audio_path, mel_spectrogram_image = update_audio_and_image(audio_path)

            sample_audio, sample_image = get_sample_audio_and_image()

            return mel_spectrogram_image, audio_path, species_name, selected_row_index, sample_audio, sample_image, suggested_specie, audio_table, date, time, comment
    return None, None, "Specie", -1, None, None, None, audio_table, None, None, "No Comments"

def apply_styles(row):
    # Check the Validation value and apply color styling to the entire row
    if row["Validation"] == 1: # Green for Validation = 1
        return ['background-color: #63C132'] * len(row)  
    elif row["Validation"] == 2: # Light green for Bird
        return ['background-color: #86b46e'] * len(row)
    elif row["Validation"] == 0: # Orange for Suggested Specie
        return ['background-color: #FFA500'] * len(row) 
    elif row["Validation"] == -1: # Red for Other = -1
        return ['background-color: #B02E0C'] * len(row)  # Red for Validation = 0
    elif row["Validation"] == -2: # light grey for Unknown
        return ['background-color: #D3D3D3'] * len(row)
    else:
        return [''] * len(row)  # Default, no styling

def get_sample_audio_and_image():
    sample_dir = Globals.get_sample_audio_dir()
    species = Globals.get_current_specie_name()
    if not sample_dir or not species:
        return None, None
    sample_audio_files = list_audio_files_from_folder(os.path.join(sample_dir, str(species)))
    if sample_audio_files:
        sample_audio, sample_image = update_audio_and_image(sample_audio_files[0])
    else:
        sample_audio = None
        sample_image = None
        print("No audio files found for the selected species")

    Globals.set_current_sample_audio_file(sample_audio)

    return sample_audio, sample_image

# Diccionario global para almacenar los estilos de las filas
row_styles = {}

def update_and_highlight_row(audio_table, validation_value, from_audio_selected=False):
    """
    Actualiza el estilo de la fila seleccionada dependiendo del valor de validación
    y resalta la fila actual.
    """
    row_corrector = -1 if from_audio_selected else 0

    current_row_index = Globals.get_current_row_index()
    next_row_index = current_row_index + 1 + row_corrector

    # Cambia los colores según el valor de validación
    if validation_value is not None:
        audio_table.at[current_row_index, "Validation"] = validation_value

    # Aplicar estilos a todas las filas basadas en su valor de validación
    styled_audio_table = audio_table.style.apply(apply_styles, axis=1)

    return styled_audio_table

def highlight_current_row(audio_table):
    # Create row lines orange style for that row
    def highlight_row(row):
        return ['border: 2px solid orange' if row.name == Globals.get_current_row_index() else '' for _ in row]
    
    return audio_table.style.apply(highlight_row, axis=1)

def update_validation(audio_table, row_index, new_value, suggestedSpecie=None):
    if 0 <= row_index < len(audio_table):
        audio_table.at[row_index, "Validation"] = new_value
        audio_table.at[row_index, "Suggested Specie"] = suggestedSpecie
        # return audio_table.style.apply(apply_styles, axis=1)
        return audio_table  # Verde para validación
    return audio_table

def check_for_updates():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            latest_version = response.json().get("tag_name")
            if latest_version:
                try:
                    update_available = Version(latest_version.lstrip("v")) > Version(
                        CURRENT_VERSION.lstrip("v")
                    )
                except InvalidVersion:
                    update_available = latest_version != CURRENT_VERSION
                if update_available:
                    return f"A new version {latest_version} is available! Please update."
    except requests.RequestException:
        pass
    return "You are using the latest version."

def build_footer():
    update_message = check_for_updates()
    with Row():
        Markdown(
            f"""
            <div style='display: flex; justify-content: space-around; align-items: center; padding: 10px; text-align: center'>
                <div>
                    <div style="display: flex;flex-direction: row;">
                        GUI version:&nbsp;<span id="current-version">{CURRENT_VERSION}</span>
                        <span id="update-available" style="display: {'inline' if 'new version' in update_message else 'none'}; color: red; margin-left: 10px;">
                            <a href="https://github.com/{GITHUB_REPO}/releases/latest" target="_blank">Update available!</a>
                        </span>
                    </div>
                </div>
            </div>
            """
        )

def tutorial_tab():
    """
    Generate the tutorial tab content.

    Returns:
    gr.Blocks: The tutorial tab content.
    """
    with Blocks() as tutorial:
        Markdown("""
        # Tutorial

        ## Purpose of the Application
        The BirdNET Predictions Validator App is designed to help validate bird species predictions generated by BirdNET. This tool allows users to view and listen to audio segments and record the accuracy of predictions in a downloadable CSV file.

        ## How to Use the Application

        ### Load Audios
        1. Navigate to the "Load Audios" tab.
        2. Select "Files" or "Folder" and click "Browse" to upload your audio files.

        ### Validate Predictions
        1. Go to the "Validate BirdNET predictions" tab.
        2. Select an audio file from the table.
        3. View the mel spectrogram and listen to the audio.
        4. Use the "Specie", "Other", and "Unknown" buttons to validate the predictions.
        5. If necessary, enter a suggested species and click "Suggested Specie".

        ### Save and Load Validations
        1. To save the validations, click "Save Table".
        2. To load previous validations from a CSV file, click "Load CSV and Copy Validation".
                    
        ## Video Tutorial
        
        """)

        embed_html = '<iframe width="560" height="315" src="https://www.youtube.com/embed/BJYW3RqA2uQ?si=SVWU3tZrFiRqfVuD" title="Tutorial" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
        HTML(embed_html)

    return tutorial
