# inky
Code to run inky display

## Installation notes
On Raspberry Pi lite (headless) install two packages
`sudo apt install libjpeg-dev libopenblas-dev`

## Local development (off-device)

The Raspberry Pi packages (`inky`, `adafruit-*`) don't build on a laptop, so a
minimal dev dependency set is provided for rendering pages without hardware:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest                       # run unit tests
.venv/bin/python preview.py            # render TidePage -> TidePage_preview.png
.venv/bin/python preview.py pages.tidePage:TidePage   # explicit page
```

`preview.py` renders any `BasePage` subclass to a PNG and does not import the
hardware packages.

## Tide chart page

The default page shows a 48-hour tide chart for Mystery Bay, WA
(NOAA station 9444971). Tide times come from NOAA in station-local Pacific time,
and the "current time" line uses the device clock — **set the Raspberry Pi's
timezone to America/Los_Angeles** so the now-line aligns with the curve.