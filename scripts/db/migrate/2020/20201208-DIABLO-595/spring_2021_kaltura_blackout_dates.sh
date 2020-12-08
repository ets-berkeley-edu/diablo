#!/bin/bash

# -------------------------------------------------------------------
#
# Script must be run with sudo
#
# -------------------------------------------------------------------

# Abort immediately if a command fails
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Sorry, you must use 'sudo' to run this script."; echo
  exit 1
fi

cd /opt/python/current/app

export PYTHONPATH=/opt/python/current/app/diablo
export DIABLO_ENV=production
export LC_ALL=en_US

source /opt/python/run/venv/bin/activate

export FLASK_APP=scripts/commands.py
flask assign_kaltura_blackout_dates

echo 'Done.'

exit 0
