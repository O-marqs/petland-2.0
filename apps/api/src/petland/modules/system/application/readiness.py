from typing import Protocol


class ReadinessProbe(Protocol):
    def is_ready(self) -> bool: ...


class CheckReadiness:
    def __init__(self, probe: ReadinessProbe) -> None:
        self._probe = probe

    def execute(self) -> bool:
        return self._probe.is_ready()
