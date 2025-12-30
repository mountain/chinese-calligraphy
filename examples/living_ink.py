# examples/living_ink.py
from PIL import Image, ImageDraw

from chinese_calligraphy import Brush, Style
from chinese_calligraphy.font import find_font_path


def get_any_font(candidates: list[str]) -> str:
    for name in candidates:
        p = find_font_path(name)
        if p:
            print(f"Using font: {p}")
            return p
    raise FileNotFoundError("No suitable font found for verification.")


def main() -> None:
    # Try generic fonts if project specific ones are missing
    font_path = get_any_font(["FZWangDXCJF", "STSong", "Songti", "PingFang SC", "Arial"])

    # Setup canvas
    w, h = 1500, 400
    img = Image.new("RGB", (w, h), (245, 240, 230))  # Paper color
    draw = ImageDraw.Draw(img)

    # Test text: repeated character to see effect clearly
    char = "墨"

    # Medium range test
    dryness_levels = [0.1, 0.2, 0.3, 0.4, 0.5]

    # Brush with consistent noise seed
    brush = Brush(seed=42)
    rng = brush.rng()

    font_size = 180
    y_pos = 100
    x_start = 150
    gap = 250

    for i, dry in enumerate(dryness_levels):
        # Create style with specific dryness
        style = Style(font_path=font_path, font_size=font_size, color=(30, 30, 30), ink_dryness=dry)

        font = style.font()

        # Position
        x = x_start + i * gap
        p = (x, y_pos)

        # Draw label
        draw.text((x, y_pos + 220), f"Dry: {dry}", fill=(100, 100, 100))

        # Standard transforms for testing
        rot, shear, scale = 0.0, 0.0, 1.0

        # Using draw_char directly to test specific params
        brush.draw_char(
            base_img=img,
            draw=draw,
            p=p,
            ch=char,
            font=font,
            fill=style.color,
            r=rng,
            rot=rot,
            shear_x=shear,
            scale=scale,
            ink_dryness=dry,  # Passing the explicit dryness
        )

    output_path = "living_ink.png"
    img.save(output_path)
    print(f"Saved verification image to {output_path}")


if __name__ == "__main__":
    main()
