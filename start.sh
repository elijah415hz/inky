#!/bin/bash
# Launched by the inky.service systemd unit. stdout/stderr flow to journald
# (view with: journalctl --user -u inky -f). -u keeps Python unbuffered so
# log lines appear promptly; exec drops the extra shell from the process tree.
PATH=/usr/local/bin:$PATH
cd /home/elijahblaisdell/inky && exec pipenv run python -u main.py
