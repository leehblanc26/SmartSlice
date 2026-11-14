
"""SmartSlice 0.1.4: offline, non-geometric Bambu 3MF settings editor."""
import json
import zipfile
from pathlib import Path

CONFIG = "Metadata/project_settings.config"
PROCESS_KEYS = ("sparse_infill_density", "sparse_infill_pattern", "wall_loops", "layer_height")
class ProjectError(ValueError):
    pass

def read_project(path):
    path = Path(path)
    if path.suffix.lower() != ".3mf":
        raise ProjectError("Only Bambu Studio 3MF projects are supported.")
    if not zipfile.is_zipfile(path):
        raise ProjectError("Not a valid 3MF ZIP archive.")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ProjectError("Duplicate archive entries; refusing ambiguous modification.")
        if CONFIG not in names:
            raise ProjectError("No Bambu Studio project_settings.config found. Save as a Bambu Studio project first.")
        try:
            data = json.loads(archive.read(CONFIG).decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ProjectError("Cannot parse Bambu project settings JSON.") from exc
        if not isinstance(data, dict):
            raise ProjectError("Unexpected Bambu project settings structure.")
        if not any(key in data for key in PROCESS_KEYS):
            raise ProjectError("No recognizable process settings in project configuration; refusing to guess.")
    return data

def proposed_changes(purpose, priority):
    # Small, explicitly experimental set of process changes. No filament or printer settings.
    if purpose not in ("Decorative", "Functional") or priority not in ("Fast", "Balanced", "Quality"):
        raise ValueError("Invalid purpose or priority")
    return {
        "sparse_infill_density": "8%" if purpose == "Decorative" else "15%",
        "sparse_infill_pattern": "adaptivecubic",
        "wall_loops": "2" if purpose == "Decorative" else "3",
        "layer_height": {"Fast": "0.28", "Balanced": "0.20", "Quality": "0.12"}[priority],
    }

def preview(path, purpose, priority):
    data = read_project(path)
    proposal = proposed_changes(purpose, priority)
    # Only edit keys already present; do not manufacture unknown schema fields.
    return {k: (data[k], v) for k,v in proposal.items() if k in data and data[k] != v}

def save_project(source, destination, purpose, priority):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ProjectError("Choose a new filename. SmartSlice never overwrites the original.")
    original = read_project(source)
    proposal = proposed_changes(purpose, priority)
    changes = {k:(original[k],v) for k,v in proposal.items() if k in original and original[k]!=v}
    if not changes:
        raise ProjectError("No applicable changes found; nothing exported.")
    revised = dict(original)
    for k,(_,value) in changes.items():
        revised[k] = value
    payload = json.dumps(revised,ensure_ascii=False,indent=2).encode("utf-8")
    # Repack without parsing or changing any model, plate, thumbnail, color or modifier data.
    with zipfile.ZipFile(source,"r") as src:
        with zipfile.ZipFile(destination,"x") as dst:
            dst.comment = src.comment
            for info in src.infolist():
                dst.writestr(info, payload if info.filename == CONFIG else src.read(info.filename))
    # Verify every untouched entry is byte-for-byte equal after decompression.
    try:
        with zipfile.ZipFile(source) as before, zipfile.ZipFile(destination) as after:
            if before.namelist() != after.namelist():
                raise ProjectError("Archive entry list changed.")
            for name in before.namelist():
                if name != CONFIG and before.read(name) != after.read(name):
                    raise ProjectError(f"Unexpected change to {name}")
            saved = json.loads(after.read(CONFIG))
            for k,(_,value) in changes.items():
                if saved.get(k) != value:
                    raise ProjectError(f"Settings verification failed for {k}")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return changes
