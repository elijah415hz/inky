# inky
Code to run inky display

## Installation notes
On Raspberry Pi lite (headless) install two packages
`sudo apt install libjpeg-dev libopenblas-dev`

## Auto-deploy (push-to-deploy)

The Pi runs the app as a systemd **user** service and polls GitHub on a timer.
When `main` moves, the Pi resets to it, syncs deps if the lockfile changed, and
restarts the display. No inbound connections — works behind Tailscale/NAT.

**Daily workflow:** develop on a feature branch, merge to `main`. The Pi picks
it up within ~2 minutes. That's it.

**One-time setup on the Pi** (the last SSH):

```bash
cd ~/inky && git pull && bash deploy/install.sh
```

Then remove the old `@reboot .../start.sh` crontab line (the installer prints it).

**Operate it:**

```bash
journalctl --user -u inky-deploy -f     # watch deploy checks
journalctl --user -u inky -f            # watch the app
systemctl --user restart inky           # manual restart
```

- **Change the tracked branch:** edit `BRANCH` at the top of `deploy/deploy.sh`.
- **Change the poll interval:** edit `OnUnitActiveSec` in
  `deploy/inky-deploy.timer`, then `systemctl --user daemon-reload &&
  systemctl --user restart inky-deploy.timer`.

If hardware access (SPI/GPIO/I²C) ever fails under the user service, fall back to
a system service with `User=` plus a single NOPASSWD sudoers line for the
restart command.

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