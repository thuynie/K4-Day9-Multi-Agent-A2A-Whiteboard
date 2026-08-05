import json
import platform
import sys
from datetime import datetime
from pathlib import Path

from ..config import FRAMEWORK_NAME, MODEL_NAME, MODEL_PARAMETER_SIZE, POLICY_VERSION


def write_metadata(path: Path, run_id: str, succeeded: int, failed: int) -> None:
    metadata = {
        "run_id": run_id,
        "generated_at": datetime.now().astimezone().isoformat(),
        "model": {"name": MODEL_NAME, "parameter_size": MODEL_PARAMETER_SIZE, "provider": "local-code"},
        "framework": {"name": FRAMEWORK_NAME, "version": "0.1.0"},
        "runtime": {
            "python_version": platform.python_version(),
            "operating_system": platform.platform(),
            "cases_processed": succeeded + failed,
            "cases_succeeded": succeeded,
            "cases_failed": failed,
        },
        "policy_version": POLICY_VERSION,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
