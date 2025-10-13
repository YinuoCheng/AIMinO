import os, re, json, time, requests
from typing import Annotated, Literal
from pydantic import BaseModel, Field, confloat, ValidationError, TypeAdapter
import napari
from qtpy import QtWidgets

# ======================
# 1) Command schema (Pydantic v2)
# ======================

Float = confloat(strict=False)

class CmdLayerVisibility(BaseModel):
    action: Literal["layer_visibility"]
    name: str
    op: Literal["show", "hide", "toggle"]

class CmdPanelToggle(BaseModel):
    action: Literal["panel_toggle"]
    name: str
    op: Literal["open", "close"]

class CmdZoomBox(BaseModel):
    action: Literal["zoom_box"]
    box: Annotated[list[Float], Field(min_length=4, max_length=4)]  # [x1,y1,x2,y2]

class CmdCenterOn(BaseModel):
    action: Literal["center_on"]
    point: Annotated[list[Float], Field(min_length=2, max_length=2)]  # [x,y]

class CmdSetZoom(BaseModel):
    action: Literal["set_zoom"]
    zoom: Float

class CmdFitToLayer(BaseModel):
    action: Literal["fit_to_layer"]
    name: str

class CmdListLayers(BaseModel):
    action: Literal["list_layers"]

class CmdHelp(BaseModel):
    action: Literal["help"]

class CmdUnknown(BaseModel):
    action: Literal["unknown"]
    text: str

Allowed = (CmdLayerVisibility | CmdPanelToggle | CmdZoomBox |
           CmdCenterOn | CmdSetZoom | CmdFitToLayer |
           CmdListLayers | CmdHelp | CmdUnknown)

ALLOWED_ADAPTER = TypeAdapter(Allowed)

# ======================
# 2) Utilities
# ======================

def find_layer(viewer, name):
    q = name.lower().strip()
    # exact first
    for ly in viewer.layers:
        if ly.name.lower() == q:
            return ly
    # fuzzy contains
    candidates = [ly for ly in viewer.layers if q in ly.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError(f"Ambiguous layer name '{name}'. Matches: {', '.join([ly.name for ly in candidates])}")
    return None

def list_layers(viewer):
    return [l.name for l in viewer.layers]

def list_panels(viewer):
    return list(viewer.window._dock_widgets.keys())

def llm_status():
    b = os.getenv("LLM_BACKEND")
    if b == "openai":
        ok = bool(os.getenv("OPENAI_API_KEY"))
        m = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return f"LLM: {'on' if ok else 'off'} (openai, model={m})"
    if b == "ollama":
        m = os.getenv("OLLAMA_MODEL", "llama3.1")
        return f"LLM: on (ollama, model={m})"
    return "LLM: off (using regex fallback)"

# ---- napari 0.6 camera-safe helpers ----
def _get_vispy_camera(viewer):
    """
    Return the underlying vispy camera across napari versions.
    0.6.x: viewer.window._qt_viewer.canvas.scene.camera
    0.4.x: viewer.window.qt_viewer.view.camera
    """
    qtv = getattr(viewer.window, "_qt_viewer", None) or getattr(viewer.window, "qt_viewer", None)
    if qtv is None:
        return None
    canvas = getattr(qtv, "canvas", None)
    if canvas is not None and hasattr(canvas, "scene"):
        cam = getattr(canvas.scene, "camera", None)
        if cam is not None:
            return cam
    view = getattr(qtv, "view", None)
    if view is not None and hasattr(view, "camera"):
        return view.camera
    return None

def set_view_box(viewer, x1, y1, x2, y2):
    """Zoom to the given world box; fallback to center+approx zoom if needed."""
    xlo, xhi = sorted([float(x1), float(x2)])
    ylo, yhi = sorted([float(y1), float(y2)])

    cam = _get_vispy_camera(viewer)
    if cam is not None and hasattr(cam, "set_range"):
        cam.set_range(x=(xlo, xhi), y=(ylo, yhi))
        return f"Zoomed to box: ({xlo:.1f},{ylo:.1f})–({xhi:.1f},{yhi:.1f})"

    # Fallback
    cx = (xlo + xhi) / 2.0
    cy = (ylo + yhi) / 2.0
    viewer.camera.center = (cx, cy)
    try:
        xs, ys = [], []
        for ly in viewer.layers:
            if not ly.visible:
                continue
            (ymin, xmin), (ymax, xmax) = ly.extent.world[0][:2], ly.extent.world[1][:2]
            xs += [xmin, xmax]; ys += [ymin, ymax]
        if xs and ys:
            full_w = max(xs) - min(xs)
            full_h = max(ys) - min(ys)
            box_w = max(1e-6, xhi - xlo)
            box_h = max(1e-6, yhi - ylo)
            scale = min(full_w / box_w, full_h / box_h) * 0.8
            viewer.camera.zoom = max(0.01, float(scale))
    except Exception:
        pass
    return f"Centered on ({cx:.1f},{cy:.1f}); set approximate zoom."

def center_on(viewer, x, y):
    viewer.camera.center = (float(x), float(y))
    return f"Centered on ({float(x):.1f}, {float(y):.1f})"

def set_zoom(viewer, z):
    viewer.camera.zoom = float(z)
    return f"Set zoom to {float(z):.2f}"

def fit_to_layer(viewer, name):
    try:
        ly = find_layer(viewer, name)
    except ValueError as e:
        return str(e)
    if not ly:
        return f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
    (ymin, xmin), (ymax, xmax) = ly.extent.world[0][:2], ly.extent.world[1][:2]
    return set_view_box(viewer, xmin, ymin, xmax, ymax)

def set_layer_visibility(viewer, name, op):
    try:
        ly = find_layer(viewer, name)
    except ValueError as e:
        return str(e)
    if not ly:
        return f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
    if op == "show":
        ly.visible = True
    elif op == "hide":
        ly.visible = False
    else:
        ly.visible = not ly.visible
    return f"{'Shown' if ly.visible else 'Hidden'} layer '{ly.name}'"

def toggle_panel(viewer, name, open_it=True):
    """Toggle panel visibility in napari viewer."""
    try:
        # Try to find the panel by name
        dock_widgets = viewer.window._dock_widgets
        if name in dock_widgets:
            widget = dock_widgets[name]
            if open_it:
                widget.show()
                return f"Opened panel '{name}'"
            else:
                widget.hide()
                return f"Closed panel '{name}'"
        else:
            available = list(dock_widgets.keys())
            return f"Panel '{name}' not found. Available panels: {', '.join(available) or '(none)'}"
    except Exception as e:
        return f"Error toggling panel '{name}': {e}"

# ======================
# 3) Regex parser (fast local)
# ======================

def parse_command_regex(text: str) -> Allowed:
    t = text.strip().lower()

    m = re.match(r"(show|hide|toggle)\s+layer\s+(.+)", t)
    if m:
        return CmdLayerVisibility(action="layer_visibility", op=m.group(1), name=m.group(2).strip())

    m = re.match(r"(open|close)\s+panel\s+(.+)", t)
    if m:
        return CmdPanelToggle(action="panel_toggle", op=m.group(1), name=m.group(2).strip())

    m = re.match(r"zoom\s+to\s+([0-9.\-]+)\s*,\s*([0-9.\-]+)\s+([0-9.\-]+)\s*,\s*([0-9.\-]+)", t)
    if m:
        x1, y1, x2, y2 = map(float, m.groups())
        return CmdZoomBox(action="zoom_box", box=[x1, y1, x2, y2])

    m = re.match(r"zoom\s+([0-9.]+)$", t)
    if m:
        return CmdSetZoom(action="set_zoom", zoom=float(m.group(1)))

    m = re.match(r"(center|centre)\s+on\s+([0-9.\-]+)\s*,\s*([0-9.\-]+)", t)
    if m:
        x, y = float(m.group(2)), float(m.group(3))
        return CmdCenterOn(action="center_on", point=[x, y])

    m = re.match(r"fit\s+to\s+layer\s+(.+)", t)
    if m:
        return CmdFitToLayer(action="fit_to_layer", name=m.group(1).strip())

    if t in {"layers", "list layers"}:
        return CmdListLayers(action="list_layers")

    if t in {"help", "?"}:
        return CmdHelp(action="help")

    return CmdUnknown(action="unknown", text=text)

# ======================
# 4) LLM backends
# ======================

SYS_PROMPT = """You convert a short user request into a JSON command for a napari viewer.
Allowed actions and JSON examples:
1) {"action":"layer_visibility","op":"show|hide|toggle","name":"<layer name>"}
2) {"action":"panel_toggle","op":"open|close","name":"<panel name>"}
3) {"action":"zoom_box","box":[x1,y1,x2,y2]}
4) {"action":"center_on","point":[x,y]}
5) {"action":"set_zoom","zoom":1.6}
6) {"action":"fit_to_layer","name":"<layer name>"}
7) {"action":"list_layers"}
8) {"action":"help"}
Rules:
- Respond with JSON ONLY. No prose.
- If unsure, return {"action":"help"}.
"""

def llm_openai(text: str) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role":"system","content":SYS_PROMPT},{"role":"user","content":text}],
        "response_format": {"type":"json_object"},
        "temperature": 0
    }
    for i in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return json.loads(r.json()["choices"][0]["message"]["content"])
        if r.status_code in (429,500,502,503,504) and i < 2:
            time.sleep(1.5*(i+1)); continue
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")

def llm_ollama(text: str) -> dict:
    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    url = f"{base}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role":"system","content":SYS_PROMPT+"\nReturn JSON only."},
                     {"role":"user","content":text}],
        "options": {"temperature": 0},
        "stream": False
    }
    for i in range(3):
        r = requests.post(url, json=payload, timeout=300)  # long first-load
        if r.status_code == 200:
            j = r.json()
            content = (j.get("message", {}) or {}).get("content") or j.get("response")
            return json.loads(content)
        if r.status_code in (429,500,502,503,504) and i < 2:
            time.sleep(1.5*(i+1)); continue
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:200]}")

def llm_parse_command(text: str) -> Allowed:
    backend = os.getenv("LLM_BACKEND", "").lower()
    if backend == "openai":
        raw = llm_openai(text)
    elif backend == "ollama":
        raw = llm_ollama(text)
    else:
        raise RuntimeError("LLM_BACKEND must be 'openai' or 'ollama'")
    try:
        return ALLOWED_ADAPTER.validate_python(raw)
    except ValidationError:
        return CmdHelp(action="help")

# ======================
# 5) Execute actions
# ======================

def execute(cmd: Allowed, viewer):
    a = cmd.action
    if a == "layer_visibility":
        return set_layer_visibility(viewer, cmd.name, cmd.op)  # type: ignore
    if a == "panel_toggle":
        return toggle_panel(viewer, cmd.name, open_it=(cmd.op == "open"))  # type: ignore
    if a == "zoom_box":
        x1, y1, x2, y2 = cmd.box  # type: ignore
        return set_view_box(viewer, x1, y1, x2, y2)
    if a == "center_on":
        x, y = cmd.point  # type: ignore
        return center_on(viewer, x, y)
    if a == "set_zoom":
        return set_zoom(viewer, cmd.zoom)  # type: ignore
    if a == "fit_to_layer":
        return fit_to_layer(viewer, cmd.name)  # type: ignore
    if a == "list_layers":
        return "Layers: " + (", ".join(list_layers(viewer)) or "(none)")
    if a == "help":
        return (
            "Examples:\n"
            "- show layer nuclei (or just 'nuclei')\n- hide layer cell\n"
            "- zoom 2   (or 'zoom to 2')\n- zoom to 100,200 600,700\n"
            "- center on 250,300\n- fit to layer exemplar\n- layers"
        )
    return "Sorry, I didn't understand. Type 'help' for examples."

# ======================
# 6) Dock widget
# ======================

class CommandDock(QtWidgets.QWidget):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.setLayout(QtWidgets.QVBoxLayout())
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Try: 'show the nuclei layer and fit the view' or 'help'")
        self.run_btn = QtWidgets.QPushButton("Run")
        self.status_label = QtWidgets.QLabel(llm_status())
        self.out = QtWidgets.QPlainTextEdit(); self.out.setReadOnly(True)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.input); row.addWidget(self.run_btn)
        self.layout().addLayout(row)
        self.layout().addWidget(self.status_label)
        self.layout().addWidget(self.out)

        self.run_btn.clicked.connect(self.on_run)
        self.input.returnPressed.connect(self.on_run)

    def write(self, msg): self.out.appendPlainText(msg)

    def on_run(self):
        text = self.input.text().strip()
        if not text: return

        # 1) fast local regex parser first
        cmd = parse_command_regex(text); src = "regex"

        # 2) if unknown → ask LLM
        if isinstance(cmd, CmdUnknown) or cmd.action == "unknown":
            try:
                cmd = llm_parse_command(text); src = "LLM"
            except Exception as e:
                self.write(f"[LLM ERROR] {e}")

        # 3) execute
        try:
            resp = execute(cmd, self.viewer)
        except Exception as e:
            resp = f"Error: {e}"

        self.write(f"> {text} [{src}]\n{resp}\n")
        self.input.clear()
        self.status_label.setText(llm_status())

# ======================
# 7) Main
# ======================

if __name__ == "__main__":
    viewer = napari.Viewer()

    # Load any demo files you have handy (edit paths as needed)
    demo_candidates = [
        "scimapExampleData/registration/exemplar-001.ome.tif",
        "scimapExampleData/segmentation/unmicst-exemplar-001/nuclei.ome.tif",
        "scimapExampleData/segmentation//unmicst-exemplar-001/cell.ome.tif",
        "exemplar-001.ome.tif", "nuclei.ome.tif", "cell.ome.tif",
        "nuclei.tif", "cell.tif",
    ]
    for p in demo_candidates:
        if os.path.exists(p):
            viewer.open(p)

    dock = CommandDock(viewer)
    viewer.window.add_dock_widget(dock, name="Command", area="right")

    napari.run()