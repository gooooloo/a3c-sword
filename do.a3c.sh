#!/bin/bash
python3 train.unix.py "$@" && tmux a -t  a3c \; select-window -t 1 \;
