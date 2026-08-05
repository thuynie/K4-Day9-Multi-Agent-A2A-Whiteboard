from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
LOGGING_DIR = ROOT_DIR / "logging"

POLICY_VERSION = "EC_POLICY_V2"
MODEL_NAME = "deterministic-python"
MODEL_PARAMETER_SIZE = "N/A"
FRAMEWORK_NAME = "custom-python-a2a"
