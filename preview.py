"""Render any BasePage subclass to a PNG for off-device preview.

Usage:
    python preview.py                       # defaults to pages.tidePage:TidePage
    python preview.py pages.tidePage:TidePage
Writes <ClassName>_preview.png in the current directory.

This harness deliberately does NOT import `inky` or `main.py`, so it runs on a
laptop without the Raspberry Pi hardware packages.
"""
import importlib
import sys


def main(spec: str) -> None:
    module_name, class_name = spec.split(":")
    module = importlib.import_module(module_name)
    page_cls = getattr(module, class_name)
    page = page_cls()
    image = page.make_image()
    out = f"{class_name}_preview.png"
    image.convert("RGB").save(out)
    print(f"Wrote {out} ({image.size[0]}x{image.size[1]})")


if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else "pages.tidePage:TidePage"
    main(spec)
