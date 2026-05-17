"""Abstract base for every Argus sense plugin."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
import time


@dataclass
class SenseData:
    """Uniform container for anything a sensor returns."""

    sensor: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    image: Optional[bytes] = None        # JPEG or PNG bytes
    audio: Optional[bytes] = None        # WAV bytes
    text: Optional[str] = None           # Human-readable summary
    error: Optional[str] = None


class SensePlugin(ABC):
    """Every sensor in Argus implements this."""

    name: str = "unknown"
    capabilities: List[str] = []          # e.g. ["capture", "stream", "detect"]

    @abstractmethod
    async def probe(self) -> bool:
        """Return True if this sensor is available on the current machine."""
        ...

    @abstractmethod
    async def read(self) -> SenseData:
        """Take a single snapshot from the sensor."""
        ...

    async def stream(self) -> AsyncIterator[SenseData]:
        """Yield continuous readings. Default: just reads in a loop."""
        while True:
            yield await self.read()

    async def close(self) -> None:
        """Release hardware / file handles."""
        pass

    def mcp_tools(self) -> List[Dict[str, Any]]:
        """Describe MCP tools this sensor exposes. Overridden per-plugin."""
        return [
            {
                "name": f"argus_{self.name}_read",
                "description": f"Read a snapshot from the {self.name} sensor",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        """Dispatch an MCP tool call to this sensor. Override if tools need args."""
        if tool_name == f"argus_{self.name}_read":
            return await self.read()
        raise ValueError(f"Unknown tool {tool_name}")
