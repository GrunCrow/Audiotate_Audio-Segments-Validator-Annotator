# Audiotate: Audio segments validator annotator

<p align="center"><img src="assets/audiotate-logo.svg" alt="Audiotate — audio annotation" width="620"></p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Framework-Gradio-orange.svg)](https://gradio.app/)
[![DOI](https://zenodo.org/badge/829889197.svg)](https://doi.org/10.5281/zenodo.19252331)

## Overview

**Audiotate: Audio Segments Validator–Annotator** is a lightweight, **Python-based application** built with **Gradio** that enables users to efficiently **annotate and validate short audio segments**.  
It is designed for **researchers, ecologists, sound analysts, and developers** who need a simple, intuitive interface to review, correct, or label short audio clips—either unlabeled samples or predictions from deep learning models (e.g., BirdNET, Perch, or any other classifiers).

Audiotate allows users to:
- Load a structured folder of audio files.
- Listen to each audio segment.
- View its spectrogram.
- Assign or edit labels (either predefined or custom).
- Add optional comments.
- Save all annotations to a **CSV file** for downstream analysis or model training.

Although originally inspired by bird sound validation workflows with BirdNET, **Audiotate** is **domain-agnostic**—it can be applied to any sound classification task, from terrestrial ecology, underwater monitoring to urban soundscape analysis.

### Citation

If you use this application, please cite the software:

```
@misc{marquez2024audiotate,
  author       = {Márquez-Rodríguez, Alba and Rollán, Laura and Pérez Gimeno, Neus},
  title        = {Audiotate: Audio segments validator annotator},
  year         = {2024},
  howpublished = {\url{https://github.com/SEANIMALMOVE/Audiotate_Audio-Segments-Validator-Annotator}},
  note         = {Version 1.8, Accessed: YYYY-MM-DD},
  doi          = {10.5281/zenodo.19252332}
}
```

A software manuscript is being prepared with the name *Audiotate: A GUI tool for human annotation and validation of audio segments*.

<!--
> Márquez-Rodríguez, Alba, Mohedano-Munoz, M. Á., Marín-Jiménez, M. J., Santamaría-García, E., Bastianelli, G., Jordano, P., & Mendoza, I.  
> **A Bird Song Detector for improving bird identification through Deep Learning: a case study from Doñana**  
> Ecological Informatics, 2025, 103254. https://doi.org/10.1016/j.ecoinf.2025.103254
-->

<!--📄 [Read the article](https://doi.org/10.1016/j.ecoinf.2025.103254)-->

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Executable Files](#executable-files)
    - [Installing on Windows and Linux](#installing-on-windows-and-linux)
    - [Running the Application](#running-the-application)
  - [Repository use](#repository-use)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Usage](#usage)
  - [Using the GUI](#using-the-gui)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Audio Playback:** Listen to `.wav` or `.mp3` files directly in the browser.
- **Spectrogram Visualization:** Each segment is displayed as a mel-spectrogram using `librosa`.
- **Annotation & Validation:** Assign labels via buttons or free text; ideal for both annotation and verification.
- **Comments:** Add notes or context to each sample.
- **CSV Export:** Save all annotations and comments in a structured `.csv` file.
- **Session Resume:** Continue where you left off—reload previous annotation sessions.
- **Cross-Platform:** Works on Windows, Linux, and macOS (through the web browser).
- **No Installation Required:** Executable versions available for easy use.

## Getting Started

### Executable Files

Standalone builds bundle Python and the application libraries. Download the latest release for your operating system:

- [Download for Windows (64-bit)](https://github.com/GrunCrow/Audiotate_Audio-Segments-Validator-Annotator/releases/latest/download/Audiotate-Windows-x86_64.exe)
- [Download for Linux (64-bit)](https://github.com/GrunCrow/Audiotate_Audio-Segments-Validator-Annotator/releases/latest/download/Audiotate-Linux-x86_64.tar.gz)

On Windows, double-click the downloaded `.exe`. On Linux, extract the `.tar.gz`, open a terminal in the extracted folder, and run:

```bash
chmod +x Audiotate-Linux-x86_64
./Audiotate-Linux-x86_64
```

The Linux build targets x86_64 systems based on Ubuntu 22.04 or newer. Both builds open Audiotate in your default browser. Annotation history is stored in your user data folder, so launching from a read-only install directory is supported.

Release executables are built on native Windows and Linux runners when a `v*` version tag is pushed. A manual build can also be started from the repository's **Actions → Build desktop executables** page.

The following video tutorial demonstrates how to use the BirdNET Predictions Validator App executable file on a Windows system. It covers the installation process, how to run the application, and a walkthrough of the graphical user interface (GUI).

[![Youtube Video Tutorial](assets/Docs/Images/video_tutorial.png)](https://youtu.be/BJYW3RqA2uQ)

#### Installing on Windows and Linux

Follow the download and launch instructions above. These are standalone builds; Python and the application libraries do not need to be installed separately.

#### Running the Application

Choose the folder containing the audio files to validate. To show reference clips, optionally select a folder containing one subfolder per label/species, with sample audio files in each subfolder.

### Repository use

#### Prerequisites

- Python 3.11 or higher
- Gradio
- Pandas
- Librosa (for audio processing)
- See more in the `environment_linux.yml`

#### Installation

1. Clone the repository:

```bash
git clone https://github.com/GrunCrow/Audiotate_Audio-Segments-Validator-Annotator.git
cd Audiotate_Audio-Segments-Validator-Annotator
```

2. Install the required packages:

```bash
pip install -r requirements-build.txt
```

#### Usage

1. Run the application:

```bash
python app.py
```

2. Open the provided link in your web browser to access the app.

### Using the GUI

1. **Prepare your audio files** in the following format:

```python
root_folder/
├── Specie1/
│ ├── audio1.wav
│ └── audio2.WAV
├── Specie2/
│ ├── audio1.wav
│ └── audio2.WAV
...
```

2. **Select Audios Folder**: Choose the folder containing the audio files.

![Load Audio Files](assets/Docs/Images/load_audio_files.png)

3. **Visualize and Play Audio**: View and listen to the audio segments. The app provides a visual representation of audio segments for easy navigation. You can listen to the audio files directly within the app.

![Visualize and Play Audio](assets/Docs/Images/visualize_segments.png)

4. **Validate Predictions**: Mark the prediction as correct or incorrect.

![Validate Predictions](assets/Docs/Images/validate.png)

5. **Download CSV**: Export the validation results as a CSV file for further analysis.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find bugs, please create an issue or submit a pull request. Your contributions can help make this app better for everyone.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

Author: Alba Márquez-Rodríguez

If you have any questions or need further assistance, please feel free to contact me in the Issues of the repository.

> Audiotate was developed as part of ongoing research into AI-assisted acoustic analysis and validation tools for ecological monitoring and sound classification.
