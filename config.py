# config.py

"""Application configuration and per-user persistent state paths."""

import os
import sys
from pathlib import Path

CURRENT_VERSION = "v1.8.4"
GITHUB_REPO = "GrunCrow/Audiotate_Audio-Segments-Validator-Annotator"

# Frozen applications can be launched from a read-only install directory or a
# random working directory. Keep annotation history in a writable user folder.
if getattr(sys, "frozen", False):
    if os.name == "nt":
        _data_root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Audiotate"
    else:
        _data_root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "Audiotate"
else:
    _data_root = Path(__file__).resolve().parent
_data_root.mkdir(parents=True, exist_ok=True)

SUGGESTED_SPECIES_FILE = str(_data_root / "suggested_species.txt")
COMMENTS_FILE = str(_data_root / "comments.txt")

class Globals:
    _sample_audio_dir = ""
    _current_specie_name = ""
    _current_sample_audio_file = ""

    _root_dir_audio_files = ""
    _audio_file_list = []
    _current_row_index = -1

    @classmethod
    def set_sample_audio_dir(cls, value):
        cls._sample_audio_dir = value

    @classmethod
    def get_sample_audio_dir(cls):
        return cls._sample_audio_dir
    
    @classmethod
    def set_current_specie_name(cls, value):
        cls._current_specie_name = value

    @classmethod
    def get_current_specie_name(cls):
        return cls._current_specie_name
    
    @classmethod
    def set_current_sample_audio_file(cls, value):
        cls._current_sample_audio_file = value

    @classmethod
    def get_current_sample_audio_file(cls):
        return cls._current_sample_audio_file
    
    @classmethod
    def set_root_dir_audio_files(cls, value):
        cls._root_dir_audio_files = value

    @classmethod
    def get_root_dir_audio_files(cls):
        return cls._root_dir_audio_files
    
    @classmethod
    def set_audio_file_list(cls, value):
        cls._audio_file_list = value

    @classmethod
    def get_audio_file_list(cls):
        return cls._audio_file_list
    
    @classmethod
    def set_current_row_index(cls, value):
        cls._current_row_index = value

    @classmethod
    def get_current_row_index(cls):
        return cls._current_row_index
