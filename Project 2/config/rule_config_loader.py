"""
Loads rule_thresholds.yaml — kept deliberately separate from Project 0's
settings.yaml, since DB credentials and rule thresholds change for
completely different reasons and shouldn't live in the same file.
"""

import yaml
from pathlib import Path

RULE_CONFIG_PATH = Path(__file__).parent / "rule_thresholds.yaml"


def load_rule_config() -> dict:
    with open(RULE_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)