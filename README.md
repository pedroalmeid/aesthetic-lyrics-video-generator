# Aesthetic Lyrics Video Generator

Generates aesthetic vertical lyric videos by synchronizing text with audio using Whisper and FFmpeg over a cycling image slideshow.

## Prerequisites

- **Python 3.10+**
- **FFmpeg** installed and accessible in your system `PATH`

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Place your input files in the corresponding folders:
   - `input/audio/` — Audio file (`.mp3`, `.wav`, `.m4a`, etc.)
   - `input/lyrics/` — Lyrics file (`.txt`, one subtitle line per line)
   - `input/img/` — Background photos (`.jpg`, `.png`, `.webp`)

2. Run the generator:

```bash
python generate_video.py
```

3. The generated video will be saved to:
   - `output/video.mp4`

## Configuration

Adjust settings at the top of [`generate_video.py`](generate_video.py):
- `LANGUAGE`: Language code for alignment (e.g. `"en"`, `"pt"`, `"es"`).
- `FPS`: Slide speed (frames/images per second).
- `LYRICS_OFFSET`: Subtitle timing adjustment in seconds (e.g. `-0.4` to display slightly before vocals).
- `DARK_OVERLAY_OPACITY`: Dim background images for better text legibility.

