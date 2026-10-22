"""Audiotate local Gradio application."""

import os
from tkinter import Tk, filedialog

import gradio as gr
import pandas as pd

from audio_processing import (
    load_audio_files_from_folder, update_audio_and_image,
    extract_time_from_filename, extract_date_from_filename,
)
from config import Globals
from data_processing import save_table_to_csv, update_table_with_validation
from species_management import (
    add_suggested_species, get_suggested_species, initialize_suggested_species_file,
    initialize_comments_file, add_comment, get_comments,
)
from ui_components import build_footer, tutorial_tab, on_audio_selected, update_validation, get_sample_audio_and_image


def _choose_path(mode):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        if mode == "Files":
            return list(filedialog.askopenfilenames(
                filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")]
            ))
        folder = filedialog.askdirectory()
        return load_audio_files_from_folder(folder) if folder else []
    finally:
        root.destroy()


def _make_audio_table(paths):
    rows = []
    for index, path in enumerate(paths, start=1):
        rows.append({
            "Idx": index,
            "File": os.path.basename(path),
            "Specie": os.path.basename(os.path.dirname(path)) or "Unlabeled",
            "Validation": -100,
            "Suggested Specie": pd.NA,
            "Comment": pd.NA,
            "Path": os.path.normpath(path),
        })
    frame = pd.DataFrame(rows, columns=[
        "Idx", "File", "Specie", "Validation", "Suggested Specie", "Comment", "Path"
    ])
    Globals.set_audio_file_list(frame)
    Globals.set_current_row_index(-1)
    return frame


def on_browse(data_type):
    try:
        paths = _choose_path(data_type)
        if not paths:
            return "No audio files selected", pd.DataFrame()
        paths = sorted(paths, key=str.casefold)
        frame = _make_audio_table(paths)
        Globals.set_root_dir_audio_files(os.path.dirname(paths[0]))
        return f"Loaded {len(frame)} audio file(s)", frame
    except Exception as exc:
        return f"Could not load audio files: {exc}", pd.DataFrame()


def on_browse_sample_audio_folder():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        folder = filedialog.askdirectory()
        if folder:
            Globals.set_sample_audio_dir(os.path.normpath(folder))
            return f"Sample folder selected: {folder}"
        return "Sample folder selection cancelled"
    finally:
        root.destroy()


def _annotate_and_advance(audio_table, selected_row_index, comment, validation, suggested_species=None):
    if audio_table is None or len(audio_table) == 0:
        return audio_table, -1, None, None, "Specie", None, None, None, None, "No Comments", gr.update()
    try:
        row = int(selected_row_index)
    except (TypeError, ValueError):
        row = -1
    if not 0 <= row < len(audio_table):
        return audio_table, -1, None, None, "Specie", None, None, None, None, "No Comments", gr.update()

    comment = comment.strip() if isinstance(comment, str) else ""
    add_comment(comment)
    audio_table.at[row, "Comment"] = comment or pd.NA
    audio_table = update_validation(audio_table, row, validation, suggested_species)
    if suggested_species:
        add_suggested_species(suggested_species)

    next_row = row + 1
    if next_row >= len(audio_table):
        Globals.set_current_row_index(row)
        return (
            audio_table, row, None, None, str(audio_table.at[row, "Specie"]),
            None, None, None, None, gr.update(choices=get_comments(), value="No Comments"),
            gr.update(choices=get_suggested_species(), value=suggested_species),
        )

    Globals.set_current_row_index(next_row)
    audio_path = audio_table.iloc[next_row]["Path"]
    species = str(audio_table.iloc[next_row]["Specie"])
    Globals.set_current_specie_name(species)
    audio, image = update_audio_and_image(audio_path)
    sample_audio, sample_image = get_sample_audio_and_image()
    Globals.set_current_sample_audio_file(sample_audio)
    return (
        audio_table, next_row, audio, image, species, sample_audio, sample_image,
        extract_date_from_filename(audio_path), extract_time_from_filename(audio_path),
        gr.update(choices=get_comments(), value="No Comments"), gr.update(choices=get_suggested_species(), value=None),
    )


def on_species_button_clicked(table, row, comment):
    return _annotate_and_advance(table, row, comment, 1)


def on_unknown_button_clicked(table, row, comment):
    return _annotate_and_advance(table, row, comment, -2)


def on_bird_button_clicked(table, row, comment):
    return _annotate_and_advance(table, row, comment, 2, "Bird")


def on_other_button_clicked(table, row, comment):
    return _annotate_and_advance(table, row, comment, -1)


def on_suggested_specie_button_clicked(table, row, species, comment):
    species = species.strip() if isinstance(species, str) else None
    if not species:
        return table, row, None, None, "Specie", None, None, None, None, comment, gr.update(choices=get_suggested_species())
    return _annotate_and_advance(table, row, comment, 0, species)


def _sample_files():
    base = Globals.get_sample_audio_dir()
    species = Globals.get_current_specie_name()
    if not base or not species:
        return []
    from audio_processing import list_audio_files_from_folder
    return list_audio_files_from_folder(os.path.join(base, species))


def _step_sample(direction):
    files = _sample_files()
    if not files:
        return None, None
    current = Globals.get_current_sample_audio_file()
    try:
        index = files.index(current)
    except ValueError:
        index = -1 if direction > 0 else 0
    path = files[(index + direction) % len(files)]
    Globals.set_current_sample_audio_file(path)
    return update_audio_and_image(path)


def main():
    initialize_suggested_species_file()
    initialize_comments_file()
    comments = get_comments() or ["No Comments"]

    with gr.Blocks(title="Audiotate — Audio annotation") as demo:
        selected_row = gr.Number(value=-1, visible=False)
        sample_audio = gr.Audio(label="Sample audio for this label", type="filepath", render=False)
        sample_image = gr.Image(label="Sample spectrogram", render=False)
        table = gr.Dataframe(
            headers=["Idx", "File", "Specie", "Validation", "Suggested Specie", "Comment", "Path"],
            type="pandas", interactive=False, render=False,
        )
        with gr.Tab("Load audio"):
            gr.Markdown("## Load audio files")
            data_type = gr.Radio(choices=["Files", "Folder"], value="Folder", label="Choose source")
            path_status = gr.Textbox(label="Status", interactive=False)
            gr.Button("Browse").click(on_browse, inputs=data_type, outputs=[path_status, table])

        with gr.Tab("Annotate"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Audio files")
                    table.render()
                    save_button = gr.Button("Save session CSV", variant="primary")
                    load_button = gr.Button("Load session CSV")
                    csv_status = gr.Textbox(value="No session loaded", label="Session status", interactive=False)
                with gr.Column():
                    gr.Markdown("## Annotation")
                    with gr.Row():
                        date_text = gr.Textbox(label="Recording date", interactive=False)
                        time_text = gr.Textbox(label="Recording time", interactive=False)
                    audio = gr.Audio(label="Audio", type="filepath", autoplay=True, loop=True)
                    spectrogram = gr.Image(label="Mel spectrogram")
                    with gr.Row():
                        species_button = gr.Button("Specie", variant="primary")
                        other_button = gr.Button("Other", variant="stop")
                    with gr.Row():
                        unknown_button = gr.Button("Unknown", variant="secondary")
                        bird_button = gr.Button("Bird", variant="secondary")
                    with gr.Row():
                        suggested_text = gr.Dropdown(choices=get_suggested_species(), label="Suggested species", interactive=True, allow_custom_value=True, filterable=True)
                        suggested_button = gr.Button("Use suggested species", variant="primary")
                    comment_box = gr.Dropdown(value="No Comments", choices=comments, label="Comment", interactive=True, allow_custom_value=True, filterable=True)

                    table.select(
                        fn=on_audio_selected, inputs=[table],
                        outputs=[spectrogram, audio, species_button, selected_row, sample_audio, sample_image,
                                 suggested_text, table, date_text, time_text, comment_box],
                    )
                    advance_outputs = [table, selected_row, audio, spectrogram, species_button, sample_audio,
                                       sample_image, date_text, time_text, comment_box, suggested_text]
                    for button, handler, inputs in (
                        (species_button, on_species_button_clicked, [table, selected_row, comment_box]),
                        (unknown_button, on_unknown_button_clicked, [table, selected_row, comment_box]),
                        (other_button, on_other_button_clicked, [table, selected_row, comment_box]),
                        (bird_button, on_bird_button_clicked, [table, selected_row, comment_box]),
                    ):
                        button.click(handler, inputs=inputs, outputs=advance_outputs)
                    suggested_button.click(
                        on_suggested_specie_button_clicked,
                        inputs=[table, selected_row, suggested_text, comment_box], outputs=advance_outputs,
                    )
                    save_button.click(save_table_to_csv, inputs=table, outputs=csv_status)
                    load_button.click(update_table_with_validation, inputs=table, outputs=[table, csv_status])
                with gr.Column():
                    gr.Markdown("## Reference audio")
                    sample_audio.render()
                    sample_image.render()
                    with gr.Row():
                        gr.Button("← Previous").click(lambda: _step_sample(-1), outputs=[sample_audio, sample_image])
                        gr.Button("Next →").click(lambda: _step_sample(1), outputs=[sample_audio, sample_image])
                    sample_status = gr.Textbox(label="Reference folder", interactive=False)
                    gr.Button("Select reference folder").click(on_browse_sample_audio_folder, outputs=sample_status)

        with gr.Tab("Tutorial"):
            tutorial_tab()
        build_footer()
        gr.Markdown("[Report an issue](https://github.com/GrunCrow/BirdNET-PredictionsValidator-App/issues)")
    return demo


if __name__ == "__main__":
    main().launch(inbrowser=True, show_api=False, server_port=7864)
