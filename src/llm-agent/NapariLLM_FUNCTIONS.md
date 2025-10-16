# Napari LLM Function Guide

## 1. Purpose
Define the exact commands an agent may execute against `napariLLM.py`, ensuring responses remain strictly JSON and focused on viewer control.

## 2. Agent Duties
- Interpret a single user request into one validated command.
- Invoke only the functions listed here; never touch image processing or filesystem tasks.
- When intent is unclear, respond with the `help` command and wait for clarification.

## 3. Runtime Facts
- The agent always controls an active napari viewer (Qt loop already running).
- Layers can originate from melanoma imaging and MCMICRO segmentation.
- Every JSON reply from a model must be validated with `ALLOWED_ADAPTER`.

## 4. Command Catalog
Each tool is defined by a name, description, and JSON schema. Wrap these as OpenAI function calls or LangChain `StructuredTool` objects. Always provide the napari `viewer` instance when calling backend functions.

### 4.1 `layer_visibility`
- **Purpose**: Change the visibility of a specific layer.
- **Backend call**: `set_layer_visibility(viewer, name, op)`
- **JSON schema**:
```json
{
  "name": "layer_visibility",
  "description": "Change the visibility of a napari layer.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Layer label (case-insensitive)."},
      "op": {"type": "string", "enum": ["show", "hide", "toggle"]}
    },
    "required": ["name", "op"]
  }
}
```

### 4.2 `panel_toggle`
- **Purpose**: Open or close a dock widget.
- **Backend call**: `toggle_panel(viewer, name, open_it)`
- **JSON schema**:
```json
{
  "name": "panel_toggle",
  "description": "Open or close a dock widget by name.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "op": {"type": "string", "enum": ["open", "close"]}
    },
    "required": ["name", "op"]
  }
}
```

### 4.3 `zoom_box`
- **Purpose**: Fit the view to a rectangular world-coordinate region.
- **Backend call**: `set_view_box(viewer, x1, y1, x2, y2)`
- **JSON schema**:
```json
{
  "name": "zoom_box",
  "description": "Fit the camera to a rectangular world-coordinate region.",
  "parameters": {
    "type": "object",
    "properties": {
      "box": {
        "type": "array",
        "items": {"type": "number"},
        "minItems": 4,
        "maxItems": 4,
        "description": "[x1, y1, x2, y2] world coordinates."
      }
    },
    "required": ["box"]
  }
}
```

### 4.4 `center_on`
- **Purpose**: Center the camera on a coordinate.
- **Backend call**: `center_on(viewer, x, y)`
- **JSON schema**:
```json
{
  "name": "center_on",
  "description": "Pan the camera to center a coordinate.",
  "parameters": {
    "type": "object",
    "properties": {
      "point": {
        "type": "array",
        "items": {"type": "number"},
        "minItems": 2,
        "maxItems": 2,
        "description": "[x, y] world coordinate."
      }
    },
    "required": ["point"]
  }
}
```

### 4.5 `set_zoom`
- **Purpose**: Apply an absolute zoom factor.
- **Backend call**: `set_zoom(viewer, zoom)`
- **JSON schema**:
```json
{
  "name": "set_zoom",
  "description": "Set the camera zoom factor.",
  "parameters": {
    "type": "object",
    "properties": {
      "zoom": {
        "type": "number",
        "minimum": 0.01,
        "description": "Absolute zoom scalar."
      }
    },
    "required": ["zoom"]
  }
}
```

### 4.6 `fit_to_layer`
- **Purpose**: Reframe the view so a layer is fully visible.
- **Backend call**: `fit_to_layer(viewer, name)`
- **JSON schema**:
```json
{
  "name": "fit_to_layer",
  "description": "Zoom and pan so an entire layer is visible.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Layer to fit."}
    },
    "required": ["name"]
  }
}
```

### 4.7 `list_layers`
- **Purpose**: Enumerate current layer names.
- **Backend call**: `list_layers(viewer)`
- **JSON schema**:
```json
{
  "name": "list_layers",
  "description": "Return all layer names currently loaded.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

### 4.8 `help`
- **Purpose**: Provide usage hints when intent is unclear.
- **Backend call**: returns a static cheat sheet via `execute()`
- **JSON schema**:
```json
{
  "name": "help",
  "description": "Request usage instructions when intent is unclear.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

### Supporting Helpers
- `find_layer(viewer, name)` — resolves names, rejects ambiguous matches.
- `list_panels(viewer)` — enumerate dock widgets before toggling.
- `_get_vispy_camera(viewer)` — internal utility used by `set_view_box`.
- `parse_command_regex(text)` — deterministic parser for offline mode.
- `llm_status()` — summarized backend state (for UI display only).

## 5. Execution Flow
1. Receive user input.
2. Run `parse_command_regex`. If it produces `CmdUnknown`, escalate to the language model.
3. Call the LLM with the system prompt below and enforce JSON output.
4. Validate the returned JSON object with `ALLOWED_ADAPTER.validate_python`.
5. Dispatch the command via `execute(cmd, viewer)`.

### System Prompt Template
```
You control a napari viewer. Respond with exactly one JSON object that matches one of these schemas:
- layer_visibility(name:str, op:show|hide|toggle)
- panel_toggle(name:str, op:open|close)
- zoom_box(box:[x1,y1,x2,y2])
- center_on(point:[x,y])
- set_zoom(zoom:float)
- fit_to_layer(name:str)
- list_layers()
- help()
If you are unsure, output {"action":"help"}.
```
Configure OpenAI with `response_format={"type":"json_object"}` or use an equivalent LangChain structured output parser.

## 6. Safety Rules
- Return descriptive error text; never expose stack traces.
- Ask for clarification when a layer or panel name is ambiguous.
- Validate coordinates and zoom factors before modifying the camera.
- Catch exceptions inside `execute()` and respond with `"Error: ..."` while keeping the session alive.

