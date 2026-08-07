# ==================== CONFIG ====================

CSV_FILE = "data.csv"
BACKGROUND_FILE = "background.png"
FONT = "Microsoft YaHei"
OUTPUT_DIR = "output"
OUTPUT_FORMAT = "jpg"

PREVIEW = True
PREVIEW_SECONDS = 0.5
PREVIEW_MAX_SCREEN_RATIO = 0.5

ID_Y = 800
ID_SIZE = 300
ID_COLOR = "#FFFFFF"
ID_STROKE_WIDTH = 14
ID_STROKE_COLOR = "#000000"

TEAM_Y = 1250
TEAM_SIZE = 300
TEAM_MAX_WIDTH = 2750
TEAM_COLOR = "#FFFFFF"
TEAM_STROKE_WIDTH = 14
TEAM_STROKE_COLOR = "#000000"

# ================================================


import csv
import re
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageTk

try:
    import winreg
except ImportError:
    winreg = None


def safe_filename(text):
    text = text.strip()
    return re.sub(r'[<>:"/\\|?*]', "_", text)


def find_system_font_path(font_name):
    if winreg is None:
        return None

    font_dir = Path(r"C:\Windows\Fonts")

    registry_paths = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
        ),
    ]

    target = font_name.lower().strip()

    for root, reg_path in registry_paths:
        try:
            with winreg.OpenKey(root, reg_path) as key:
                count = winreg.QueryInfoKey(key)[1]

                for i in range(count):
                    name, value, _ = winreg.EnumValue(key, i)

                    if target in name.lower():
                        font_path = Path(value)

                        if not font_path.is_absolute():
                            font_path = font_dir / font_path

                        if font_path.exists():
                            return str(font_path)

        except FileNotFoundError:
            pass

    return None


def resolve_font_source(font_value):
    system_font_path = find_system_font_path(font_value)

    if system_font_path:
        return system_font_path

    local_path = Path(font_value)

    if local_path.exists() and local_path.is_file():
        return str(local_path)

    raise FileNotFoundError(
        f'Could not load font "{font_value}". '
        f"Tried system font name first, then local file path."
    )


def normalize_output_format(value):
    value = value.lower().strip()

    if value in ("jpg", "jpeg"):
        return "jpg", "JPEG"

    if value == "png":
        return "png", "PNG"

    raise ValueError('OUTPUT_FORMAT must be "jpg" or "png".')


def fit_font_to_width(
    draw,
    font_source,
    text,
    base_size,
    max_width,
    stroke_width,
):
    font = ImageFont.truetype(font_source, base_size)

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width,
    )

    width = bbox[2] - bbox[0]

    if width <= max_width:
        return font

    low = 1
    high = base_size

    while low <= high:
        size = (low + high) // 2
        test_font = ImageFont.truetype(font_source, size)

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=test_font,
            stroke_width=stroke_width,
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            low = size + 1
        else:
            high = size - 1

    return ImageFont.truetype(font_source, max(1, high))


def get_centered_x(draw, image_width, text, font, stroke_width):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width,
    )

    text_width = bbox[2] - bbox[0]

    return (image_width - text_width) / 2 - bbox[0]


def create_preview(root, image):
    max_width = int(root.winfo_screenwidth() * PREVIEW_MAX_SCREEN_RATIO)
    max_height = int(root.winfo_screenheight() * PREVIEW_MAX_SCREEN_RATIO)

    preview = image.copy()
    preview.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS,
    )

    return ImageTk.PhotoImage(preview)


def main():
    output_ext, pil_save_format = normalize_output_format(OUTPUT_FORMAT)

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    background = Image.open(BACKGROUND_FILE).convert("RGBA")

    font_source = resolve_font_source(FONT)

    id_font = ImageFont.truetype(font_source, ID_SIZE)

    root = None
    preview_label = None

    if PREVIEW:
        root = tk.Tk()
        root.title("Preview")

        preview_label = tk.Label(root)
        preview_label.pack()

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            id_text = row["id"].strip()
            team_text = row["name"].strip()

            image = background.copy()
            draw = ImageDraw.Draw(image)

            id_x = get_centered_x(
                draw,
                image.width,
                id_text,
                id_font,
                ID_STROKE_WIDTH,
            )

            draw.text(
                (id_x, ID_Y),
                id_text,
                font=id_font,
                fill=ID_COLOR,
                stroke_width=ID_STROKE_WIDTH,
                stroke_fill=ID_STROKE_COLOR,
            )

            team_font = fit_font_to_width(
                draw,
                font_source,
                team_text,
                TEAM_SIZE,
                TEAM_MAX_WIDTH,
                TEAM_STROKE_WIDTH,
            )

            team_x = get_centered_x(
                draw,
                image.width,
                team_text,
                team_font,
                TEAM_STROKE_WIDTH,
            )

            draw.text(
                (team_x, TEAM_Y),
                team_text,
                font=team_font,
                fill=TEAM_COLOR,
                stroke_width=TEAM_STROKE_WIDTH,
                stroke_fill=TEAM_STROKE_COLOR,
            )

            filename = safe_filename(
                f"{id_text}_{team_text}.{output_ext}"
            )

            output_path = output_dir / filename

            if pil_save_format == "JPEG":
                image.convert("RGB").save(
                    output_path,
                    format="JPEG",
                    quality=95,
                )
            else:
                image.save(
                    output_path,
                    format="PNG",
                )

            print(f"Generated: {filename}")

            if PREVIEW:
                preview_image = create_preview(root, image)

                preview_label.config(image=preview_image)
                preview_label.image = preview_image

                root.update_idletasks()
                root.update()

                time.sleep(PREVIEW_SECONDS)

    if PREVIEW and root is not None:
        root.destroy()


if __name__ == "__main__":
    main()
