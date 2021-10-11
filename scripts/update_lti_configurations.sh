#!/bin/bash

# -------------------------------------------------------------------
#
# Kaltura LTI repointing
#
# -------------------------------------------------------------------

# Abort immediately if a command fails
set -e

echo; echo "Welcome!"; echo

if [ "$EUID" -ne 0 ]; then
  echo "Sorry, you must use 'sudo' to run this script."; echo
  exit 1
fi

cd /var/app/current

export PYTHONPATH=/var/app/venv/staging-LQM1lest/bin
export DIABLO_ENV=production
export LC_ALL=en_US

source "${PYTHONPATH}/activate"

echo "Running 'update_lti'..."; echo

FLASK_APP=scripts/commands.py flask update_lti

echo; echo "Done!"; echo

exit 0
