from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def _parse_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lower()
    if v.startswith("0x"):
        v = v[2:]
    if v.startswith("#"):
        v = v[1:]
    if len(v) != 6:
        raise ValueError(f"invalid rgb: {value}")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def _recolor_rgba(image: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    img = image.convert("RGBA")
    alpha = img.getchannel("A")
    out = Image.new("RGBA", img.size, rgb + (0,))
    out.putalpha(alpha)
    return out


def recolor_ico_file(path: Path, rgb: tuple[int, int, int]) -> bool:
    original = Image.open(path)
    ico = getattr(original, "ico", None)

    if ico is not None:
        sizes = sorted(ico.sizes(), key=lambda s: (s[0], s[1]))
        base_size = max(sizes, key=lambda s: (s[0], s[1]))
        base_img = _recolor_rgba(ico.getimage(base_size), rgb)
        base_img.save(path, format="ICO", sizes=sizes)
        return True

    recolored = _recolor_rgba(original, rgb)
    recolored.save(path, format="ICO")
    return True


def recolor_png_file(path: Path, rgb: tuple[int, int, int]) -> bool:
    original = Image.open(path)
    recolored = _recolor_rgba(original, rgb)
    recolored.save(path, format="PNG")
    return True


def recolor_image_file(path: Path, rgb: tuple[int, int, int]) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".ico":
        return recolor_ico_file(path, rgb)
    if suffix == ".png":
        return recolor_png_file(path, rgb)
    raise ValueError(f"unsupported file type: {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="icons")
    parser.add_argument("--color", default="7F7F7F")
    parser.add_argument("--exts", default="ico")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    rgb = _parse_rgb(args.color)
    exts = [
        e.strip().lower().lstrip(".")
        for e in str(args.exts).split(",")
        if e.strip()
    ]

    changed = 0
    for ext in exts:
        for p in root.rglob(f"*.{ext}"):
            if p.is_file():
                if recolor_image_file(p, rgb):
                    changed += 1

    print(f"recolored: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
