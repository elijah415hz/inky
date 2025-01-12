#!/bin/bash
PATH=/usr/local/bin:$PATH
echo $PATH > /home/elijahblaisdell/logs/cronlog
cd /home/elijahblaisdell/inky && pipenv run python main.py >> /home/elijahblaisdell/logs/cronlog 2>&1
