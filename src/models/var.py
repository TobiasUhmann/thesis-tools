from dataclasses import dataclass


@dataclass(frozen=True)
class Var:
    name: str