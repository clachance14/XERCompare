"""Explicit, portable quality settings. JSON data only, never executable rules."""

from dataclasses import dataclass, field, asdict
import json
import math
from pathlib import Path

RULES = {
    "open_ends": ("Missing predecessor or successor", 5.0, "%"),
    "leads": ("Negative relationship lag", 0.0, "%"),
    "lags": ("Positive relationship lag", 5.0, "%"),
    "non_fs": ("Non-FS relationships", 10.0, "%"),
    "hard_constraints": ("Hard constraints", 5.0, "%"),
    "high_float": ("High total float", 5.0, "%"),
    "negative_float": ("Negative total float", 0.0, "count"),
    "high_duration": ("High original duration", 5.0, "%"),
    "invalid_dates": ("Invalid stored dates", 0.0, "count"),
    "missing_resources": ("Missing resource assignments", 0.0, "count"),
    "missed_finish": ("Missed planned finish (proxy)", 5.0, "%"),
    "out_of_sequence": ("Out-of-sequence suspects", 0.0, "count"),
    "riding_date": ("Remaining start on data date", 0.0, "count"),
    "dangling_start": ("Start lacks an incoming FS/SS link", 0.0, "count"),
    "dangling_finish": ("Finish lacks an outgoing FS/FF link", 0.0, "count"),
}


@dataclass(frozen=True)
class QualityProfile:
    name: str = "Standard review"
    high_float_days: float = 44.0
    high_duration_days: float = 44.0
    limits: dict = field(default_factory=dict)
    disabled: tuple = ()

    def validate(self):
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or len(self.name) > 120
        ):
            raise ValueError("Profile name must contain 1 to 120 characters.")
        if not isinstance(self.limits, dict) or not isinstance(
            self.disabled, (tuple, list)
        ):
            raise ValueError("Invalid profile checks or limits.")
        if set(self.limits) - RULES.keys() or set(self.disabled) - RULES.keys():
            raise ValueError("Profile contains an unknown check.")
        for key, value in {
            "high_float_days": self.high_float_days,
            "high_duration_days": self.high_duration_days,
            **self.limits,
        }.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{key}: enter a finite, nonnegative number.")
            if key in RULES and RULES[key][2] == "%" and value > 100:
                raise ValueError(f"{key}: percentage must be between 0 and 100.")
        return self

    def limit(self, key):
        return self.limits.get(key, RULES[key][1])


def save_profile(profile, path):
    profile.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(profile), indent=2, allow_nan=False), encoding="utf-8"
    )


def load_profile(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["disabled"] = tuple(data.get("disabled", ()))
        return QualityProfile(**data).validate()
    except (TypeError, KeyError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid quality profile: {error}") from error
