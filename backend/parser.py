import re
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = re.compile(r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEFS])\s+([^:]+):[ \t]*(.*)$')
SUBMODULE = re.compile(r'^\[([^\]\r\n]+)\]')

def extract_submodule(message):
    match = SUBMODULE.match(message)
    return (match[1], message[match.end():]) if match else (None, message)

def parse(raw, year, timezone):
    raw = raw.rstrip('\r\n')
    match = BASE.match(raw)
    if not match:
        return {'raw_line': raw, 'error': 'Invalid threadtime format or continuation/truncated line'}
    stamp, pid, tid, level, tag, message = match.groups()
    try:
        local = datetime.strptime(f'{year}-{stamp}', '%Y-%m-%d %H:%M:%S.%f')
        zone = ZoneInfo(timezone)
        aware = local.replace(tzinfo=zone)
        if aware.utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
            raise ValueError('Ambiguous or nonexistent local time')
        timestamp = int(aware.timestamp() * 1000)
    except ValueError as exc:
        return {'raw_line': raw, 'error': str(exc)}
    submodule, body = extract_submodule(message)
    return dict(timestamp=timestamp, pid=int(pid), tid=int(tid), level=level,
                tag=tag.rstrip(), submodule=submodule, message=message,
                message_body=body, raw_line=raw, error=None)
