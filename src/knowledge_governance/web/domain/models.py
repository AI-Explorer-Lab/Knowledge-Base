from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    id: str
    display_name: str
