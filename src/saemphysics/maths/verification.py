from dataclasses import dataclass


@dataclass(frozen=True)
class MathCheck:
    name: str
    passed: bool
    details: str
