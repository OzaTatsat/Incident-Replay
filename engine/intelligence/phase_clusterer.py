"""
Phase Clusterer — groups events by MITRE ATT&CK tactic, computes
phase time boundaries, and produces per-phase summaries for the API.
"""

from __future__ import annotations
from collections import defaultdict

# MITRE tactic order (approximate kill chain)
TACTIC_ORDER = [
    "reconnaissance",
    "initial_access",
    "execution",
    "persistence",
    "privilege_escalation",
    "defense_evasion",
    "credential_access",
    "discovery",
    "lateral_movement",
    "collection",
    "command_and_control",
    "exfiltration",
    "impact",
    "unknown",
]

DISPLAY_NAMES = {
    "reconnaissance":      "Reconnaissance",
    "initial_access":      "Initial Access",
    "execution":           "Execution",
    "persistence":         "Persistence",
    "privilege_escalation":"Privilege Escalation",
    "defense_evasion":     "Defense Evasion",
    "credential_access":   "Credential Access",
    "discovery":           "Discovery",
    "lateral_movement":    "Lateral Movement",
    "collection":          "Collection",
    "command_and_control": "Command & Control",
    "exfiltration":        "Exfiltration",
    "impact":              "Impact",
    "unknown":             "Uncategorised",
}


def assign_phase(event: dict, ttps: list[dict]) -> str:
    """
    Assign the primary attack phase (MITRE tactic) to an event.
    Picks the tactic from matched TTPs that comes earliest in the kill chain,
    preferring higher-confidence matches.
    """
    if not ttps:
        # Heuristic fallback based on event type
        etype = event.get("event_type", "")
        if etype in ("process_create", "dns_query"):
            img = (event.get("image_name") or "").lower()
            if img in ("systeminfo.exe", "ipconfig.exe", "whoami.exe",
                       "nltest.exe", "arp.exe", "tasklist.exe", "netstat.exe"):
                return "discovery"
        return "unknown"

    # Sort by kill-chain order, prefer higher confidence when tied
    def sort_key(t):
        tactic = t.get("tactic", "unknown")
        idx = TACTIC_ORDER.index(tactic) if tactic in TACTIC_ORDER else 99
        return (idx, -t.get("confidence", 0))

    best = sorted(ttps, key=sort_key)[0]
    return best.get("tactic", "unknown")


def cluster_phases(enriched_events: list[dict], investigation_id: str) -> list[dict]:
    """
    Given a list of events with `phase` and `ttp_codes` already set,
    compute per-phase summaries for the DB.
    """
    phase_events = defaultdict(list)
    for ev in enriched_events:
        phase_events[ev["phase"]].append(ev)

    results = []
    for phase_name, evs in phase_events.items():
        if not evs:
            continue
        timestamps = [e["timestamp"] for e in evs]
        # Collect all technique codes seen in this phase
        all_ttps: set[str] = set()
        for ev in evs:
            codes = ev.get("ttp_codes", "")
            if codes:
                all_ttps.update(codes.split(","))
        all_ttps.discard("")

        # Confidence = share of events with score > 20
        flagged = sum(1 for ev in evs if ev.get("suspicion_score", 0) > 20)
        confidence = flagged / len(evs) if evs else 0

        results.append({
            "investigation_id": investigation_id,
            "phase_name":       phase_name,
            "display_name":     DISPLAY_NAMES.get(phase_name, phase_name.title()),
            "start_ts":         min(timestamps),
            "end_ts":           max(timestamps),
            "event_count":      len(evs),
            "key_techniques":   ",".join(sorted(all_ttps)[:8]),
            "confidence":       round(confidence, 3),
        })

    # Sort by kill-chain order
    results.sort(key=lambda p: TACTIC_ORDER.index(p["phase_name"])
                  if p["phase_name"] in TACTIC_ORDER else 99)
    return results
