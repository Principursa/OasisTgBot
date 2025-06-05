from typing import Callable, Optional, Dict, Any, List
import inspect

_PY_TO_JSON_TYPE = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

def _infer_parameters(func: Callable) -> Dict[str, Any]:
    """Generate a minimal parameters schema from a function signature."""
    sig = inspect.signature(func)

    properties: Dict[str, Dict[str, str]] = {}
    required: List[str] = []

    for name, param in sig.parameters.items():
        # Skip *args / **kwargs
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        # Resolve JSON schema type from annotation (default → string)
        anno = param.annotation
        json_type = _PY_TO_JSON_TYPE.get(anno, "string") if anno is not inspect._empty else "string"

        properties[name] = {"type": json_type}

        # Required if no default value supplied
        if param.default is param.empty:
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }

def tool(_func: Optional[Callable] = None, *, name: Optional[str] = None, description: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> Callable:
    """Decorator that marks an *instance method* as an OpenAI-ish tool.
    """

    def decorator(func: Callable):
        nonlocal parameters

        if parameters is None:
            parameters = _infer_parameters(func)

        spec = {
            "type": "function",
            "function": {
                "name": name or func.__name__,
                "description": description or (func.__doc__ or ""),
                "parameters": parameters,
            },
        }

        setattr(func, "_tool_spec", spec)
        return func

    if _func is not None and callable(_func):
        return decorator(_func)
    return decorator