#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")"

if [ -f "./venv/bin/activate" ]; then
  source "./venv/bin/activate"
fi

python ./scripts/get_calendar.py
python ./scripts/pokemon.py
python ./scripts/filter_calendar.py
