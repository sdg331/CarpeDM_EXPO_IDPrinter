"""Create the project-owned neutral formal-suit RGBA template.

The drawing is intentionally vector-like and contains no face, skin, person,
or external artwork.  Run this script whenever the source geometry changes.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "profile" / "suit_neutral.png"
SCALE = 3
WIDTH, HEIGHT = 720, 960


def points(values):
    return [(round(x * SCALE), round(y * SCALE)) for x, y in values]


def main() -> None:
    image = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    navy = (24, 45, 78, 255)
    navy_dark = (15, 30, 55, 255)
    navy_light = (43, 70, 108, 255)
    shirt = (248, 250, 253, 255)
    shirt_shadow = (218, 227, 239, 255)
    blue = (44, 94, 190, 255)

    # Broad, straight tailoring keeps the template neutral and works for every visitor.
    draw.polygon(points([(0, 960), (0, 625), (70, 520), (250, 446), (330, 505), (360, 586), (360, 960)]), fill=navy)
    draw.polygon(points([(720, 960), (720, 625), (650, 520), (470, 446), (390, 505), (360, 586), (360, 960)]), fill=navy)
    draw.polygon(points([(241, 458), (319, 472), (360, 535), (401, 472), (479, 458), (454, 960), (266, 960)]), fill=shirt)

    # Collar and lapels cover the neck seam without entering the face region.
    draw.polygon(points([(250, 446), (320, 465), (360, 535), (292, 505), (262, 546), (205, 477)]), fill=shirt_shadow)
    draw.polygon(points([(470, 446), (400, 465), (360, 535), (428, 505), (458, 546), (515, 477)]), fill=shirt_shadow)
    draw.polygon(points([(250, 446), (330, 505), (290, 642), (170, 507)]), fill=navy_light)
    draw.polygon(points([(470, 446), (390, 505), (430, 642), (550, 507)]), fill=navy_light)
    draw.line(points([(170, 507), (290, 642), (225, 960)]), fill=navy_dark, width=4 * SCALE)
    draw.line(points([(550, 507), (430, 642), (495, 960)]), fill=navy_dark, width=4 * SCALE)

    # A restrained blue tie links the template to the kiosk's blue UI.
    draw.polygon(points([(336, 523), (360, 548), (384, 523), (377, 576), (343, 576)]), fill=blue)
    draw.polygon(points([(343, 574), (377, 574), (396, 790), (360, 835), (324, 790)]), fill=(35, 76, 158, 255))

    draw.line(points([(76, 576), (63, 960)]), fill=(71, 92, 120, 150), width=3 * SCALE)
    draw.line(points([(644, 576), (657, 960)]), fill=(71, 92, 120, 150), width=3 * SCALE)

    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, optimize=True)
    print(f"wrote {OUT} ({image.mode} {image.size[0]}x{image.size[1]})")


if __name__ == "__main__":
    main()
