import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceWriter:
    def __init__(self, path: Path, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def write(self, case_id: str | None, agent: str, event: str, status: str, summary: dict[str, Any] | None = None) -> None:
        record = {
            "run_id": self.run_id,
            "timestamp": datetime.now().astimezone().isoformat(),
            "case_id": case_id,
            "agent": agent,
            "event": event,
            "status": status,
            "summary": summary or {},
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
