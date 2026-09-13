#!/bin/sh
[ -f ~/.Xresources ] && xrdb -merge ~/.Xresources
exec dbus-run-session -- /home/aios/.config/aios-session.sh
