import json
from typing import Any, Callable, Dict


ToolHandler = Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, ToolHandler] = {}

    def register(self, name: str) -> Callable[[ToolHandler], ToolHandler]:
        def decorator(func: ToolHandler) -> ToolHandler:
            self._handlers[name] = func
            return func

        return decorator

    def has(self, name: str) -> bool:
        return name in self._handlers

    def execute(self, name: str, arguments: str) -> str:
        if name not in self._handlers:
            raise ValueError(f"Tool not registered: {name}")
        handler = self._handlers[name]
        payload = json.loads(arguments) if arguments else {}
        result = handler(payload)
        if isinstance(result, str):
            return result
        return json.dumps(result)


tool_registry = ToolRegistry()
