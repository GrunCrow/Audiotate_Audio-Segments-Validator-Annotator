"""Small persistent histories used to speed up repeated annotations."""

import os

import pandas as pd

from config import SUGGESTED_SPECIES_FILE, COMMENTS_FILE


def _read_csv(path, columns):
    try:
        if os.path.exists(path):
            frame = pd.read_csv(path)
            for column in columns:
                if column not in frame:
                    frame[column] = 0 if column == "count" else ""
            return frame[columns].dropna(how="all")
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        pass
    return pd.DataFrame(columns=columns)


def initialize_suggested_species_file():
    frame = _read_csv(SUGGESTED_SPECIES_FILE, ["species", "count"])
    frame["count"] = pd.to_numeric(frame["count"], errors="coerce").fillna(0).astype(int)
    frame.to_csv(SUGGESTED_SPECIES_FILE, index=False)


def add_suggested_species(species):
    species = str(species or "").strip()
    if not species:
        return
    frame = _read_csv(SUGGESTED_SPECIES_FILE, ["species", "count"])
    frame["count"] = pd.to_numeric(frame["count"], errors="coerce").fillna(0).astype(int)
    matches = frame["species"].astype(str).str.casefold() == species.casefold()
    if matches.any():
        frame.loc[matches, "count"] += 1
    else:
        frame.loc[len(frame)] = [species, 1]
    frame.sort_values("count", ascending=False, kind="stable").to_csv(SUGGESTED_SPECIES_FILE, index=False)


def get_suggested_species():
    frame = _read_csv(SUGGESTED_SPECIES_FILE, ["species", "count"])
    frame["count"] = pd.to_numeric(frame["count"], errors="coerce").fillna(0)
    return frame.sort_values("count", ascending=False, kind="stable")["species"].astype(str).tolist()


def initialize_comments_file():
    frame = _read_csv(COMMENTS_FILE, ["Comment"])
    frame.to_csv(COMMENTS_FILE, index=False)


def add_comment(comment):
    comment = str(comment or "").strip()
    if not comment:
        return
    frame = _read_csv(COMMENTS_FILE, ["Comment"])
    if not frame["Comment"].astype(str).str.casefold().eq(comment.casefold()).any():
        frame.loc[len(frame)] = [comment]
        frame.to_csv(COMMENTS_FILE, index=False)


def get_comments():
    return _read_csv(COMMENTS_FILE, ["Comment"])["Comment"].dropna().astype(str).tolist()
