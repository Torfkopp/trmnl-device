import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dateutil.rrule import rrulestr

# Filter monthly
def filter_monthly():
    """ Returns start and end datetime for the current month """
    now = datetime.now()
    month = now.month

    first_day = now.replace(day=1)
    last_day = first_day + timedelta(days=32)
    while last_day.month != month: last_day -= timedelta(days=1)

    first_day_weekday = first_day.weekday()
    calendar_start = first_day - timedelta(days=first_day_weekday)
    added_days = 42 - (first_day_weekday + last_day.day)
    calendar_end = last_day + timedelta(days=added_days)
    

    calendar_start = calendar_start.replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
    calendar_end = calendar_end.replace(hour=23, minute=59, second=59, microsecond=999999).astimezone()

    return calendar_start, calendar_end

# Filter weekly
def filter_weekly():
    """ Returns start and end datetime for the current week """
    now = datetime.now()
    end = now + timedelta(days=7)

    calendar_start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
    calendar_end = end.replace(hour=23, minute=59, second=59, microsecond=999999).astimezone()
    
    return calendar_start, calendar_end

def event_filter(event):
    """ Filters the event, return False if it should be included """
    _ = event
    return False

def event_sort(events):
    """ Sorts events by start time """
    return sorted(events, key=lambda x: x['start'])

def recurring_event(event, dt_start_key, dt_end_key, start, end):
    """ Changes reccurint events to list of single events """
    # Birthdays before 1970 are not in ISO format and thus boom
    rrule = event.get("RRULE")
    if not "UNTIL" in rrule: 
        rrule += f";UNTIL={end.astimezone(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    
    events = list(rrulestr(s=rrule, dtstart=datetime.fromisoformat(event.get(dt_start_key)).astimezone()))
    
    events = [x for x in events if start <= x <= end]
    
    events = [{
        "start": x,
        "end": x + (datetime.fromisoformat(event.get(dt_end_key)) - datetime.fromisoformat(event.get(dt_start_key))),
        "summary": event.get("SUMMARY"),
        "description": event.get("DESCRIPTION"),
        "all_day": not "T" in event.get(dt_start_key),
        "kind": event.get("kind", "private")
    } for x in events]
    
    return events
    
    
def read_ics_file(path):
    raw = Path(path).read_bytes()
    raw = raw.replace(b'\r\n ', b'').replace(b'\r\n\t', b'')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def filter_calendar(start, end):
    """ Filters calendar events between start and end datetime """
    
    filtered_events = []
    def add_events(events, kind):
        events = events.split("BEGIN:VEVENT")[1:]
        for e in events:
            ics_dic = {}
            for line in e.splitlines():
                line = line.strip()
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                ics_dic[k] = v
            
            #if event_filter(ics_dic): continue
            
            # Every event has a DTSTART, but DTEND is optional
            dt_start_key = next((x for x in ics_dic if x.startswith("DTSTART")), None)
            if not dt_start_key: continue
            dt_end_key = next((x for x in ics_dic if x.startswith("DTEND")), dt_start_key)
            
            if "RRULE" in ics_dic:
                if ics_dic.get("RRULE").startswith("FREQ=YEARLY"): 
                    ics_dic[dt_start_key] = "2025" + ics_dic[dt_start_key][4:]
                    ics_dic[dt_end_key] = "2025" + ics_dic[dt_end_key][4:]
                else:
                    event_list = recurring_event(ics_dic, dt_start_key, dt_end_key, start, end)
                    if not event_list: continue
                    for event in event_list: filtered_events.append(event)
                    continue
                
            time_start = datetime.fromisoformat(ics_dic.get(dt_start_key)).astimezone()
            time_end = datetime.fromisoformat(ics_dic.get(dt_end_key)).astimezone()
            if time_end < start or end < time_start: continue
            
            event = {
                "start": time_start,
                "end": time_end,
                "summary": ics_dic.get("SUMMARY"),
                "description": ics_dic.get("DESCRIPTION"),
                "all_day": not "T" in ics_dic.get(dt_start_key),
                "kind": kind
            }
        
            filtered_events.append(event)
    
    events_private = read_ics_file("ics/basic.ics")
    events_football = read_ics_file("ics/football.ics")
    feiertage = read_ics_file("ics/feiertage.ics")
    
    add_events(events_private, "private")
    add_events(events_football, "football")
    add_events(feiertage, "feiertage")
    
    return event_sort(filtered_events)
    
    
if __name__ == "__main__":
    start, end = filter_weekly()
    filtered = filter_calendar(start, end)
    with open("data/weekly.json", mode="w", encoding="utf-8") as file:
        file.write(json.dumps(filtered, indent=4, default=str, ensure_ascii=False))
    
    start, end = filter_monthly()
    filtered = filter_calendar(start, end)
    with open("data/monthly.json", mode="w", encoding="utf8") as file:
        file.write(json.dumps(filtered, indent=4, default=str, ensure_ascii=False))
    
