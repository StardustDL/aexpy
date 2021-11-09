from datetime import datetime, timedelta
from .models import PayloadLog
import json
from dataclasses import asdict


def serialize(log: PayloadLog, **kwargs) -> str:
    result = asdict(log)
    result["duration"] = log.duration.total_seconds()
    result["time"] = log.time.isoformat()
    return json.dumps(result, **kwargs)


def deserialize(text) -> PayloadLog:
    raw = json.loads(text)
    raw["duration"] = timedelta(seconds=raw["duration"])
    raw["time"] = datetime.fromisoformat(raw["time"])
    return PayloadLog(**raw)
