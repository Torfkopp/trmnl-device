#!/bin/bash
set -euo pipefail

cd /app

run_tasks() {
  if [ $(date +%H) -eq 8 ]; then
    > /app/script.log
  fi
  echo "[$(date --iso-8601=seconds)] Starting scheduled run" >> /app/script.log
  python ./scripts/get_calendar.py >> /app/script.log 2>&1
  python ./scripts/pokemon.py >> /app/script.log 2>&1
  python ./scripts/filter_calendar.py >> /app/script.log 2>&1
  echo "[$(date --iso-8601=seconds)] Finished scheduled run" >> /app/script.log
}

next_delay() {
  python3 - <<'PY'
import datetime
now = datetime.datetime.now()
hours = [8, 11, 14, 17, 20]
for h in hours:
    candidate = now.replace(hour=h, minute=40, second=0, microsecond=0)
    if candidate > now:
        print(int((candidate - now).total_seconds()))
        break
else:
    tomorrow = now + datetime.timedelta(days=1)
    candidate = tomorrow.replace(hour=8, minute=40, second=0, microsecond=0)
    print(int((candidate - now).total_seconds()))
PY
}

echo "Starting scheduler in Docker. Logs will be appended to /app/script.log"
while true; do
  delay=$(next_delay)
  echo "[$(date --iso-8601=seconds)] Sleeping ${delay}s until next run" >> /app/script.log
  sleep "${delay}"
  run_tasks
done
