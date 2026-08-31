import glob
import os
import subprocess
from PIL import Image, ImageOps
import stable_whisper

# Language for lyrics alignment (e.g. "en", "pt", "es")
LANGUAGE = "en"

# Video dimensions (3:4 vertical aspect ratio)
WIDTH = 1080
HEIGHT = 1440
FPS = 3  # Images shown per second (ultra-fast slide effect)

# Visual styling
DARK_OVERLAY_OPACITY = 0.22  # Black overlay opacity on images

FONTS_DIR = "fonts"
FONT_NAME = "TikTok Sans SemiBold"
FONT_SIZE = 15

# Subtitle timing offset in seconds
# Negative value advances the text so it appears slightly before the vocals (e.g. -0.4s)
LYRICS_OFFSET = -0.4

# Directory configurations
INPUT_AUDIO_DIR = "input/audio"
INPUT_IMG_DIR = "input/img"
INPUT_LYRICS_DIR = "input/lyrics"
OUTPUT_DIR = "output"
TEMP_DIR = "temp_frames"


def get_first_file(directory: str, extensions: tuple) -> str:
    """Finds the first file in a directory matching the given extensions."""
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
    if not files:
        raise FileNotFoundError(f"No valid file found in '{directory}' with extensions {extensions}")
    return files[0]


def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
    return float(result.stdout.strip())


def align_lyrics(audio_path: str, lyrics_path: str, subtitles_path: str):
    print(f"[1/4] Aligning lyrics to audio with Whisper (language: '{LANGUAGE}')...")
    with open(lyrics_path, "r", encoding="utf-8") as f:
        lyrics = f.read()

    model = stable_whisper.load_model("base")
    # original_split=True guarantees that each line from lyrics.txt is treated as an indivisible subtitle unit
    aligned_result = model.align(audio_path, lyrics, language=LANGUAGE, original_split=True)

    # Advance or delay subtitles relative to the audio
    if LYRICS_OFFSET != 0:
        aligned_result.offset_time(LYRICS_OFFSET)

    aligned_result.to_ass(subtitles_path, segment_level=True, word_level=False)
    print(f"Subtitles file created: {subtitles_path}")


def prepare_frames(images_dir: str, target_count: int, temp_dir: str):
    print("[2/4] Processing images into 3:4 frames...")
    os.makedirs(temp_dir, exist_ok=True)

    extensions = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    raw_images = []
    for ext in extensions:
        raw_images.extend(glob.glob(os.path.join(images_dir, ext)))

    if not raw_images:
        raise FileNotFoundError(f"No images found in '{images_dir}' directory.")

    image_pool = (raw_images * ((target_count // len(raw_images)) + 1))[:target_count]

    for idx, img_path in enumerate(image_pool):
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            fitted = ImageOps.fit(img, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)

            # Apply dark overlay if configured
            if DARK_OVERLAY_OPACITY > 0:
                black_layer = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
                fitted = Image.blend(fitted, black_layer, DARK_OVERLAY_OPACITY)

            fitted.save(os.path.join(temp_dir, f"frame_{idx:05d}.jpg"), quality=90)


def render_video(audio_path: str, subtitles_path: str, output_path: str):
    print("[3/4] Rendering video with FFmpeg...")
    # Alignment=10 centers text vertically and horizontally in SSA/ASS
    # BorderStyle=1, Outline=0, Shadow=0 removes any border or shadow
    subtitle_style = (
        f"Fontname={FONT_NAME},"
        f"FontSize={FONT_SIZE},"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=0,"
        "Shadow=0,"
        "Alignment=10,"
        "MarginL=60,"
        "MarginR=60,"
        "MarginV=0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(TEMP_DIR, "frame_%05d.jpg"),
        "-i", audio_path,
        "-vf", f"subtitles={subtitles_path}:fontsdir={FONTS_DIR}:force_style='{subtitle_style}'",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)


def cleanup(subtitles_path: str):
    print("[4/4] Cleaning up temporary files...")
    for frame in glob.glob(os.path.join(TEMP_DIR, "*.jpg")):
        os.remove(frame)
    if os.path.exists(TEMP_DIR):
        os.rmdir(TEMP_DIR)
    if os.path.exists(subtitles_path):
        os.remove(subtitles_path)


def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        audio_path = get_first_file(INPUT_AUDIO_DIR, ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg"))
        lyrics_path = get_first_file(INPUT_LYRICS_DIR, ("*.txt",))
        output_video_path = os.path.join(OUTPUT_DIR, "video.mp4")
        subtitles_file = os.path.join(OUTPUT_DIR, "temp_subtitles.ass")

        print(f"Loaded audio:  {audio_path}")
        print(f"Loaded lyrics: {lyrics_path}")

        duration = get_audio_duration(audio_path)
        total_frames = int(duration * FPS)

        align_lyrics(audio_path, lyrics_path, subtitles_file)
        prepare_frames(INPUT_IMG_DIR, total_frames, TEMP_DIR)
        render_video(audio_path, subtitles_file, output_video_path)
        cleanup(subtitles_file)

        print(f"\nDone! Output saved to: {output_video_path}")
    except Exception as e:
        print(f"\nPipeline failed: {e}")


if __name__ == "__main__":
    main()