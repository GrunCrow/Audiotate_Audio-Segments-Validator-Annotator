"""CSV import and export helpers for annotation sessions."""

from tkinter import Tk, filedialog

import pandas as pd


def load_csv_and_copy_validation(audio_table):
    root = None
    try:
        root = Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return audio_table, "Load cancelled"

        saved = pd.read_csv(file_path)
        missing = {"File", "Validation"}.difference(saved.columns)
        if missing:
            raise ValueError(f"CSV is missing required column(s): {', '.join(sorted(missing))}")
        for column in ("Suggested Specie", "Comment", "Re-review"):
            if column not in saved:
                saved[column] = False if column == "Re-review" else pd.NA
        saved["Re-review"] = saved["Re-review"].fillna(False).map(
            lambda value: value if isinstance(value, bool) else str(value).strip().lower() in {"true", "1", "yes", "y"}
        )
        result = audio_table.copy()
        if "Specie" in result and "Specie" in saved:
            # Filenames often repeat across label folders, so use the label as
            # part of the key whenever both exports provide it.
            saved["_session_key"] = saved["Specie"].astype(str) + "\0" + saved["File"].astype(str)
            result["_session_key"] = result["Specie"].astype(str) + "\0" + result["File"].astype(str)
            keyed = saved.drop_duplicates("_session_key", keep="last").set_index("_session_key")
            file_keyed = saved.drop_duplicates("File", keep="last").set_index("File")
        else:
            keyed = saved.drop_duplicates("File", keep="last").set_index("File")
            file_keyed = keyed
        for column in ("Validation", "Suggested Specie", "Comment", "Re-review"):
            if column not in result:
                result[column] = -100 if column == "Validation" else (False if column == "Re-review" else pd.NA)
            values = result["_session_key"].map(keyed[column]) if "_session_key" in result else result["File"].map(keyed[column])
            if "_session_key" in result:
                values = values.combine_first(result["File"].map(file_keyed[column]))
            result[column] = values.combine_first(result[column])
        result = result.drop(columns=["_session_key"], errors="ignore")
        return result, "Validation values loaded"
    except Exception as exc:
        return audio_table, f"ERROR: {exc}"
    finally:
        if root is not None:
            root.destroy()


def save_table_to_csv(audio_table):
    root = None
    try:
        root = Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return "Save operation cancelled"
        audio_table.drop(columns=["Path"], errors="ignore").to_csv(file_path, index=False)
        return f"Validation saved to {file_path}"
    except Exception as exc:
        return f"ERROR: Could not save validation: {exc}"
    finally:
        if root is not None:
            root.destroy()


def update_table_with_validation(audio_table):
    return load_csv_and_copy_validation(audio_table)
