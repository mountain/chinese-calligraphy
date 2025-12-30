# examples/blur.py
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
    font_path = get_any_font(["FZWangDXCJF", "STSong", "Songti", "PingFang SC", "Arial"])

    w, h = 1500, 400
    img = Image.new("RGB", (w, h), (245, 240, 230))
    draw = ImageDraw.Draw(img)

    char = "暈"  # "Halo/Dizzy/Blur"

    # Test varying blur sigma
    blur_levels = [0.0, 0.5, 1.0, 2.0, 3.0]

    brush = Brush(seed=42)
    rng = brush.rng()

    font_size = 180
    y_pos = 100
    x_start = 120
    gap = 250

    for i, blur in enumerate(blur_levels):
        style = Style(
            font_path=font_path,
            font_size=font_size,
            color=(30, 30, 30),
            ink_dryness=0.05,  # Use best practice dryness
            blur_sigma=blur,
        )

        font = style.font()
        x = x_start + i * gap
        p = (x, y_pos)

        draw.text((x, y_pos + 220), f"Blur: {blur}", fill=(100, 100, 100))

        brush.draw_char(
            base_img=img,
            draw=draw,
            p=p,
            ch=char,
            font=font,
            fill=style.color,
            r=rng,
            rot=0.0,
            shear_x=0.0,
            scale=1.0,
            ink_dryness=style.ink_dryness,
            blur_sigma=style.blur_sigma,
        )

    output_path = "../blur.png"
    img.save(output_path)
    print(f"Saved blur verification image to {output_path}")


if __name__ == "__main__":
    main()
