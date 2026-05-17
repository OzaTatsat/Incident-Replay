"""
Sysmon log parser — handles:
  - Single Sysmon XML event files
  - Multi-event XML files (wrapped in <Events> root)
  - EVTX binary files (via python-evtx)

Normalises every event into a consistent dict for the intelligence layer.
"""

from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree

# Sysmon XML namespace
NS = "http://schemas.microsoft.com/win/2004/08/events/event"


# ── Public API ──────────────────────────────────────────────────────────────────

def parse_file(filepath: str) -> list[dict]:
    """
    Auto-detect format (XML vs EVTX) and return list of normalised event dicts.
    """
    p = Path(filepath)
    suffix = p.suffix.lower()
    if suffix == ".evtx":
        return _parse_evtx(filepath)
    else:
        return _parse_xml(filepath)


# ── XML Parsing ─────────────────────────────────────────────────────────────────

def _parse_xml(filepath: str) -> list[dict]:
    raw = Path(filepath).read_bytes()

    # Strip BOM if present
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]

    events = []
    try:
        root = etree.fromstring(raw)
    except etree.XMLSyntaxError:
        # Try wrapping in a root element — some exports are concatenated events
        raw = b"<Events>" + raw + b"</Events>"
        root = etree.fromstring(raw)

    tag_local = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    if tag_local == "Event":
        norm = _normalise_event(root)
        if norm:
            events.append(norm)
    else:
        # Root is <Events> or similar container
        for elem in root.iter(f"{{{NS}}}Event"):
            norm = _normalise_event(elem)
            if norm:
                events.append(norm)

    return sorted(events, key=lambda e: e["timestamp"])


def _parse_evtx(filepath: str) -> list[dict]:
    try:
        import Evtx.Evtx as evtx
        import Evtx.Views as ev
    except ImportError:
        raise RuntimeError("python-evtx not installed: pip install python-evtx")

    events = []
    with evtx.Evtx(filepath) as log:
        for record in log.records():
            try:
                xml_str = record.xml()
                root = etree.fromstring(xml_str.encode())
                norm = _normalise_event(root)
                if norm:
                    events.append(norm)
            except Exception:
                continue
    return sorted(events, key=lambda e: e["timestamp"])


# ── Normalisation ───────────────────────────────────────────────────────────────

# Sysmon Event ID → internal event_type string
EVENT_TYPE_MAP = {
    1:  "process_create",
    2:  "file_create_time",
    3:  "network_connect",
    5:  "process_terminate",
    6:  "driver_load",
    7:  "image_load",
    8:  "create_remote_thread",
    10: "process_access",
    11: "file_create",
    12: "registry_create",
    13: "registry_set",
    14: "registry_rename",
    15: "file_stream_create",
    17: "pipe_create",
    18: "pipe_connect",
    22: "dns_query",
    23: "file_delete",
    25: "process_tamper",
    26: "file_delete_detected",
}

def _normalise_event(elem) -> dict | None:
    """Convert a raw <Event> XML element to a clean normalised dict."""
    try:
        sys_elem  = elem.find(f"{{{NS}}}System")
        data_elem = elem.find(f"{{{NS}}}EventData")

        if sys_elem is None:
            return None

        event_id_el = sys_elem.find(f"{{{NS}}}EventID")
        if event_id_el is None:
            return None
        event_id = int(event_id_el.text)

        # Only handle Sysmon operational events
        if event_id not in EVENT_TYPE_MAP:
            return None

        # Timestamp
        tc = sys_elem.find(f"{{{NS}}}TimeCreated")
        ts_ms = _parse_timestamp(tc.get("SystemTime") if tc is not None else None)
        if ts_ms is None:
            return None

        # EventData key-value pairs
        fields = {}
        if data_elem is not None:
            for data in data_elem:
                name = data.get("Name")
                if name:
                    fields[name] = (data.text or "").strip()

        event_type = EVENT_TYPE_MAP[event_id]
        normalised = _build_normalised(event_id, event_type, fields)
        normalised["timestamp"] = ts_ms
        normalised["event_type"] = event_type
        normalised["sysmon_event_id"] = event_id
        normalised["raw_fields"] = fields
        normalised["summary"] = _build_summary(event_type, fields)

        return normalised

    except Exception:
        return None


def _build_normalised(event_id: int, event_type: str, f: dict) -> dict:
    """Extract the key fields per event type into a flat dict."""
    def exe(key="Image"):
        val = f.get(key, "")
        return val.split("\\")[-1] if val else ""

    if event_type == "process_create":
        return {
            "image":         f.get("Image", ""),
            "image_name":    exe("Image"),
            "cmd":           f.get("CommandLine", ""),
            "parent_image":  f.get("ParentImage", ""),
            "parent_name":   exe("ParentImage"),
            "parent_cmd":    f.get("ParentCommandLine", ""),
            "user":          f.get("User", ""),
            "pid":           f.get("ProcessId", ""),
            "parent_pid":    f.get("ParentProcessId", ""),
            "integrity":     f.get("IntegrityLevel", ""),
            "hashes":        f.get("Hashes", ""),
            "process_guid":  f.get("ProcessGuid", ""),
            "parent_guid":   f.get("ParentProcessGuid", ""),
        }
    elif event_type == "network_connect":
        return {
            "image":          f.get("Image", ""),
            "image_name":     exe("Image"),
            "dest_ip":        f.get("DestinationIp", ""),
            "dest_hostname":  f.get("DestinationHostname", ""),
            "dest_port":      f.get("DestinationPort", ""),
            "src_ip":         f.get("SourceIp", ""),
            "src_port":       f.get("SourcePort", ""),
            "protocol":       f.get("Protocol", "tcp"),
            "user":           f.get("User", ""),
            "initiated":      f.get("Initiated", ""),
            "process_guid":   f.get("ProcessGuid", ""),
        }
    elif event_type in ("registry_set", "registry_create", "registry_rename"):
        return {
            "image":          f.get("Image", ""),
            "image_name":     exe("Image"),
            "target_object":  f.get("TargetObject", ""),
            "details":        f.get("Details", ""),
            "user":           f.get("User", ""),
            "process_guid":   f.get("ProcessGuid", ""),
        }
    elif event_type == "process_access":
        return {
            "source_image":   f.get("SourceImage", ""),
            "source_name":    exe("SourceImage"),
            "target_image":   f.get("TargetImage", ""),
            "target_name":    exe("TargetImage"),
            "granted_access": f.get("GrantedAccess", ""),
            "call_trace":     f.get("CallTrace", ""),
            "source_guid":    f.get("SourceProcessGUID", ""),
            "target_guid":    f.get("TargetProcessGUID", ""),
        }
    elif event_type == "dns_query":
        return {
            "image":        f.get("Image", ""),
            "image_name":   exe("Image"),
            "query_name":   f.get("QueryName", ""),
            "query_results":f.get("QueryResults", ""),
            "user":         f.get("User", ""),
            "process_guid": f.get("ProcessGuid", ""),
        }
    elif event_type == "file_create":
        return {
            "image":        f.get("Image", ""),
            "image_name":   exe("Image"),
            "target_file":  f.get("TargetFilename", ""),
            "creation_utc": f.get("CreationUtcTime", ""),
            "user":         f.get("User", ""),
            "process_guid": f.get("ProcessGuid", ""),
        }
    elif event_type == "image_load":
        return {
            "image":      f.get("Image", ""),
            "image_name": exe("Image"),
            "image_loaded":f.get("ImageLoaded", ""),
            "signed":     f.get("Signed", ""),
            "signature":  f.get("Signature", ""),
            "hashes":     f.get("Hashes", ""),
        }
    elif event_type in ("create_remote_thread", "process_tamper"):
        return {
            "source_image": f.get("SourceImage", ""),
            "source_name":  exe("SourceImage"),
            "target_image": f.get("TargetImage", ""),
            "target_name":  exe("TargetImage"),
            "start_address":f.get("StartAddress", ""),
            "start_module": f.get("StartModule", ""),
        }
    else:
        return {k: v for k, v in f.items()}


def _build_summary(event_type: str, f: dict) -> str:
    exe = lambda k: (f.get(k, "") or "").split("\\")[-1]
    if event_type == "process_create":
        parent = exe("ParentImage")
        child  = exe("Image")
        cmd    = (f.get("CommandLine", "") or "")[:80]
        return f"{parent} → {child}: {cmd}"
    elif event_type == "network_connect":
        img  = exe("Image")
        dst  = f.get("DestinationIp", "") or f.get("DestinationHostname", "")
        port = f.get("DestinationPort", "")
        return f"{img} → {dst}:{port}"
    elif event_type in ("registry_set", "registry_create"):
        img = exe("Image")
        key = (f.get("TargetObject", "") or "")[-60:]
        return f"{img} wrote {key}"
    elif event_type == "process_access":
        src = exe("SourceImage")
        tgt = exe("TargetImage")
        acc = f.get("GrantedAccess", "")
        return f"{src} accessed {tgt} [{acc}]"
    elif event_type == "dns_query":
        img = exe("Image")
        q   = f.get("QueryName", "")
        return f"{img} queried {q}"
    elif event_type == "file_create":
        img = exe("Image")
        tgt = (f.get("TargetFilename", "") or "")[-60:]
        return f"{img} created {tgt}"
    else:
        return event_type.replace("_", " ").title()


def _parse_timestamp(ts_str: str | None) -> int | None:
    """Parse ISO-8601 / Sysmon timestamp → Unix milliseconds."""
    if not ts_str:
        return None
    ts_str = ts_str.rstrip("Z").replace(" ", "T")
    # Truncate sub-second to 6 digits for fromisoformat
    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?", ts_str)
    if not match:
        return None
    base = match.group(1)
    frac = match.group(2) or ""
    frac = frac[:7]  # up to 6 decimal places
    try:
        dt = datetime.fromisoformat(f"{base}{frac}").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None
