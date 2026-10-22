"""Audiotate local Gradio application."""

import os
from tkinter import Tk, filedialog

import gradio as gr
import pandas as pd

# Gradio 4.44.1's API-info generation can pass boolean JSON Schema values to
# gradio_client.utils.get_type(), which assumes every schema is a dictionary.
# Keep API metadata generation from failing on those valid JSON Schema values.
from gradio_client import utils as gradio_client_utils

_gradio_get_type = gradio_client_utils.get_type


def _get_gradio_schema_type(schema):
    if isinstance(schema, bool):
        return "boolean"
    return _gradio_get_type(schema)


gradio_client_utils.get_type = _get_gradio_schema_type

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
from ui_components import build_footer, tutorial_tab, on_audio_selected, update_validation, get_sample_audio_and_image, style_validation_table


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
            "Re-review": False,
            "Path": os.path.normpath(path),
        })
    frame = pd.DataFrame(rows, columns=[
        "Idx", "File", "Specie", "Validation", "Suggested Specie", "Comment", "Re-review", "Path"
    ])
    Globals.set_audio_file_list(frame)
    Globals.set_current_row_index(-1)
    return frame


def on_browse(data_type):
    try:
        paths = _choose_path(data_type)
        if not paths:
            empty = pd.DataFrame()
            return "No audio files selected", empty, empty
        paths = sorted(paths, key=str.casefold)
        frame = _make_audio_table(paths)
        Globals.set_root_dir_audio_files(os.path.dirname(paths[0]))
        return f"Loaded {len(frame)} audio file(s)", frame, style_validation_table(_visible_session(frame))
    except Exception as exc:
        empty = pd.DataFrame()
        return f"Could not load audio files: {exc}", empty, empty


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


def _visible_session(session, only_flagged=False):
    if session is None:
        return pd.DataFrame()
    if only_flagged and "Re-review" in session:
        view = session[session["Re-review"].fillna(False).astype(bool)].copy()
    else:
        view = session.copy()
    return view.reindex(columns=["Idx", "File", "Specie", "Validation", "Suggested Specie", "Comment", "Path"])


def _filter_session(session, only_flagged):
    view = _visible_session(session, only_flagged)
    status = f"Showing {len(view)} flagged audio(s)" if only_flagged else f"Showing all {len(view)} audio(s)"
    return style_validation_table(view), status


def _toggle_review_flag(session, row, only_flagged):
    try:
        row = int(row)
    except (TypeError, ValueError):
        row = -1
    if session is None or not 0 <= row < len(session):
        return session, style_validation_table(_visible_session(session, only_flagged)), "Select an audio row first.", gr.update(value="Flag for re-review")
    if "Re-review" not in session:
        session["Re-review"] = False
    session.at[row, "Re-review"] = not bool(session.at[row, "Re-review"])
    status = "Selected audio flagged for re-review." if session.at[row, "Re-review"] else "Re-review flag cleared."
    label = "Clear re-review flag" if session.at[row, "Re-review"] else "Flag for re-review"
    return session, style_validation_table(_visible_session(session, only_flagged)), status, gr.update(value=label)


def _flag_button_update(session, row):
    try:
        row = int(row)
    except (TypeError, ValueError):
        row = -1
    flagged = (session is not None and 0 <= row < len(session)
               and bool(session.iloc[row].get("Re-review", False)))
    return gr.update(value="Clear re-review flag" if flagged else "Flag for re-review")


def _on_table_selected(session, visible_table, evt: gr.SelectData):
    if session is None or visible_table is None or visible_table.empty or not evt or not evt.index:
        return None, None, "Specie", -1, None, None, None, None, None, "No Comments", gr.update(value="Flag for re-review")
    visible_row = int(evt.index[0])
    if visible_row < 0 or visible_row >= len(visible_table):
        return None, None, "Specie", -1, None, None, None, None, None, "No Comments", gr.update(value="Flag for re-review")
    selected_idx = visible_table.iloc[visible_row]["Idx"]
    matches = session.index[session["Idx"] == selected_idx].tolist()
    if not matches:
        return None, None, "Specie", -1, None, None, None, None, None, "No Comments", gr.update(value="Flag for re-review")
    result = on_audio_selected(session, type("Selection", (), {"index": (matches[0], 0)})())
    flagged = bool(session.iloc[matches[0]].get("Re-review", False))
    label = "Clear re-review flag" if flagged else "Flag for re-review"
    return (*result[:7], *result[8:], gr.update(value=label))


def _load_audio_for_row(session, row):
    if session is None or not 0 <= row < len(session):
        return None, None, "Specie", None, None, None, None, None, "No Comments"
    audio_path = session.iloc[row]["Path"]
    species = str(session.iloc[row]["Specie"])
    Globals.set_current_row_index(row)
    Globals.set_current_specie_name(species)
    audio, image = update_audio_and_image(audio_path)
    sample_audio, sample_image = get_sample_audio_and_image()
    return (audio, image, species, extract_date_from_filename(audio_path),
            extract_time_from_filename(audio_path), sample_audio, sample_image,
            session.iloc[row].get("Suggested Specie"), session.iloc[row].get("Comment", "No Comments"))


def _annotate_and_advance(audio_table, selected_row_index, comment, validation, suggested_species=None, only_flagged=False):
    if audio_table is None or len(audio_table) == 0:
        return audio_table, style_validation_table(audio_table), -1, None, None, "Specie", None, None, None, None, "No Comments", "", gr.update(visible=False), gr.update(), _flag_button_update(audio_table, -1)
    try:
        row = int(selected_row_index)
    except (TypeError, ValueError):
        row = -1
    if not 0 <= row < len(audio_table):
        return audio_table, style_validation_table(audio_table), -1, None, None, "Specie", None, None, None, None, "No Comments", "", gr.update(visible=False), gr.update(), _flag_button_update(audio_table, -1)

    comment = comment.strip() if isinstance(comment, str) else ""
    add_comment(comment)
    audio_table.at[row, "Comment"] = comment or pd.NA
    audio_table = update_validation(audio_table, row, validation, suggested_species)
    if "Re-review" not in audio_table:
        audio_table["Re-review"] = False
    audio_table.at[row, "Re-review"] = False
    if suggested_species:
        add_suggested_species(suggested_species)

    unreviewed = audio_table.index[audio_table["Validation"].fillna(-100).astype(int) == -100].tolist()
    flagged = audio_table.index[audio_table["Re-review"].fillna(False).astype(bool)].tolist()
    completed = not unreviewed
    if only_flagged:
        candidates = [item for item in flagged if item > row]
        next_row = candidates[0] if candidates else (flagged[0] if flagged else None)
        if next_row is None and unreviewed:
            next_row = unreviewed[0]
    else:
        candidates = [item for item in unreviewed if item > row]
        next_row = candidates[0] if candidates else (row + 1 if row + 1 < len(audio_table) else None)
    if completed and (next_row is None or (only_flagged and not flagged)):
        Globals.set_current_row_index(row)
        if flagged:
            message = f"All audios have been reviewed. {len(flagged)} audio(s) are flagged for re-review. Review them before saving?"
            gr.Info(message, duration=None)
        else:
            message = "All audios have been reviewed. You can save the session now."
            gr.Info(message, duration=None)
        reset_filter = only_flagged and not flagged
        return (audio_table, style_validation_table(_visible_session(audio_table, False if reset_filter else only_flagged)), row,
                None, None, str(audio_table.at[row, "Specie"]), None, None, None, None,
                gr.update(choices=get_comments(), value="No Comments"), message, gr.update(visible=bool(flagged)),
                gr.update(value=False) if reset_filter else gr.update(), _flag_button_update(audio_table, row))
    if next_row is None:
        next_row = row
    audio, image, species, date, time, sample_audio, sample_image, next_suggestion, _ = _load_audio_for_row(audio_table, next_row)
    Globals.set_current_sample_audio_file(sample_audio)
    view = _visible_session(audio_table, only_flagged)
    return (audio_table, style_validation_table(view), next_row, audio, image, species, sample_audio,
            sample_image, date, time, gr.update(choices=get_comments(), value="No Comments"), "",
            gr.update(visible=False), gr.update(), _flag_button_update(audio_table, next_row))


def on_species_button_clicked(table, row, comment, only_flagged):
    return _annotate_and_advance(table, row, comment, 1, only_flagged=only_flagged)


def on_unknown_button_clicked(table, row, comment, only_flagged):
    return _annotate_and_advance(table, row, comment, -2, only_flagged=only_flagged)


def on_bird_button_clicked(table, row, comment, only_flagged):
    return _annotate_and_advance(table, row, comment, 2, "Bird", only_flagged)


def on_other_button_clicked(table, row, comment, only_flagged):
    return _annotate_and_advance(table, row, comment, -1, only_flagged=only_flagged)


def on_suggested_specie_button_clicked(table, row, species, comment, only_flagged):
    species = species.strip() if isinstance(species, str) else None
    if not species:
        return table, style_validation_table(_visible_session(table, only_flagged)), row, None, None, "Specie", None, None, None, None, comment, "Choose a suggested species first.", gr.update(visible=False), gr.update(), _flag_button_update(table, row)
    return _annotate_and_advance(table, row, comment, 0, species, only_flagged)


def _begin_flagged_review(session):
    flagged = session.index[session["Re-review"].fillna(False).astype(bool)].tolist()
    if not flagged:
        gr.Info("There are no audios flagged for re-review.")
        return session, style_validation_table(_visible_session(session)), -1, None, None, "Specie", None, None, None, None, "No Comments", "No flagged audio found.", gr.update(value=False), _flag_button_update(session, -1)
    row = flagged[0]
    loaded = _load_audio_for_row(session, row)
    audio, image, species, date, time, sample_audio, sample_image, suggestion, comment = loaded
    return (session, style_validation_table(_visible_session(session, True)), row,
            audio, image, species, sample_audio, sample_image, date, time,
            comment if isinstance(comment, str) and comment else "No Comments",
            f"Reviewing flagged audio 1 of {len(flagged)}.", gr.update(value=True), _flag_button_update(session, row))


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


def _load_table_with_validation(audio_table):
    updated_table, status = update_table_with_validation(audio_table)
    return updated_table, style_validation_table(_visible_session(updated_table)), status


def main():
    initialize_suggested_species_file()
    initialize_comments_file()
    comments = get_comments() or ["No Comments"]

    with gr.Blocks(title="Audiotate — Audio annotation") as demo:
        session_table = gr.State(pd.DataFrame(columns=["Idx", "File", "Specie", "Validation", "Suggested Specie", "Comment", "Re-review", "Path"]))
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
            gr.Button("Browse").click(on_browse, inputs=data_type, outputs=[path_status, session_table, table])

        with gr.Tab("Annotate"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Audio files")
                    table.render()
                    only_flagged = gr.Checkbox(label="Show only audios flagged for re-review", value=False)
                    filter_status = gr.Textbox(label="Session view", interactive=False)
                    only_flagged.change(_filter_session, inputs=[session_table, only_flagged], outputs=[table, filter_status])
                    review_flagged_button = gr.Button("Review flagged audios before saving", visible=False, variant="primary")
                    completion_message = gr.Markdown()
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
                        flag_review_button = gr.Button("Flag for re-review", variant="secondary")
                    with gr.Row():
                        suggested_text = gr.Dropdown(choices=get_suggested_species(), label="Suggested species", interactive=True, allow_custom_value=True, filterable=True)
                        suggested_button = gr.Button("Use suggested species", variant="primary")
                    comment_box = gr.Dropdown(value="No Comments", choices=comments, label="Comment", interactive=True, allow_custom_value=True, filterable=True)

                    table.select(
                        fn=_on_table_selected, inputs=[session_table, table],
                        outputs=[spectrogram, audio, species_button, selected_row, sample_audio, sample_image,
                                 suggested_text, date_text, time_text, comment_box, flag_review_button],
                    )
                    flag_review_button.click(
                        _toggle_review_flag, inputs=[session_table, selected_row, only_flagged],
                        outputs=[session_table, table, filter_status, flag_review_button], queue=False,
                    )
                    advance_outputs = [session_table, table, selected_row, audio, spectrogram, species_button,
                                       sample_audio, sample_image, date_text, time_text, comment_box,
                                       completion_message, review_flagged_button, only_flagged, flag_review_button]
                    for button, handler, inputs in (
                        (species_button, on_species_button_clicked, [session_table, selected_row, comment_box, only_flagged]),
                        (unknown_button, on_unknown_button_clicked, [session_table, selected_row, comment_box, only_flagged]),
                        (other_button, on_other_button_clicked, [session_table, selected_row, comment_box, only_flagged]),
                        (bird_button, on_bird_button_clicked, [session_table, selected_row, comment_box, only_flagged]),
                    ):
                        button.click(handler, inputs=inputs, outputs=advance_outputs)
                    suggested_button.click(
                        on_suggested_specie_button_clicked,
                        inputs=[session_table, selected_row, suggested_text, comment_box, only_flagged], outputs=advance_outputs,
                    )
                    review_flagged_button.click(
                        _begin_flagged_review, inputs=session_table,
                        outputs=[session_table, table, selected_row, audio, spectrogram, species_button,
                                 sample_audio, sample_image, date_text, time_text, comment_box,
                                 completion_message, only_flagged, flag_review_button],
                    )
                    save_button.click(save_table_to_csv, inputs=session_table, outputs=csv_status)
                    load_button.click(
                        _load_table_with_validation, inputs=session_table, outputs=[session_table, table, csv_status]
                    )
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
    main().launch(inbrowser=True, show_api=False, server_port=7869)
