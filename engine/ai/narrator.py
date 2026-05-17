"""
AI Narrator — stub for now, Ollama integration added later.
Returns rule-based narration templates until Ollama is wired in.
"""

from __future__ import annotations
from datetime import datetime, timezone


async def narrate_phase(phase_name: str, display_name: str,
                        events: list[dict], techniques: list[str]) -> str:
    return _template_narration(phase_name, display_name, events, techniques)


async def generate_summary(investigation_name: str, phases: list[dict],
                            total_events: int, duration_minutes: float) -> str:
    return _template_summary(investigation_name, phases, total_events, duration_minutes)


# ── Templates ───────────────────────────────────────────────────────────────────

PHASE_TEMPLATES = {
    "initial_access": (
        "The attacker gained initial access to the environment. {techniques} "
        "were observed during this phase across {count} events spanning {duration}. "
        "This is the entry point of the attack chain."
    ),
    "execution": (
        "Malicious code execution occurred during this phase. {techniques} "
        "were leveraged across {count} events over {duration}. "
        "The attacker used these techniques to run their payload on the target system."
    ),
    "persistence": (
        "The attacker established persistence mechanisms to survive reboots. "
        "{techniques} were observed in {count} events over {duration}. "
        "These techniques ensure the attacker maintains access after system restarts."
    ),
    "privilege_escalation": (
        "Privilege escalation activity was detected across {count} events over {duration}. "
        "{techniques} were used. The attacker attempted to gain higher-level permissions "
        "to expand their access within the environment."
    ),
    "defense_evasion": (
        "The attacker actively worked to avoid detection during this phase. "
        "{techniques} were observed across {count} events over {duration}. "
        "These techniques are commonly used to bypass security controls and hinder forensic analysis."
    ),
    "credential_access": (
        "Credential harvesting activity was detected. {techniques} were observed "
        "across {count} events over {duration}. The attacker targeted credential stores "
        "to enable lateral movement and persistence."
    ),
    "discovery": (
        "Internal reconnaissance activity was observed across {count} events over {duration}. "
        "{techniques} were used to enumerate the environment — including users, "
        "network configuration, and running processes — prior to lateral movement."
    ),
    "lateral_movement": (
        "The attacker moved laterally within the network during this phase. "
        "{techniques} were observed across {count} events over {duration}. "
        "This indicates the attacker is expanding their foothold beyond the initial compromise."
    ),
    "collection": (
        "Data collection activity was detected across {count} events over {duration}. "
        "{techniques} were used. The attacker staged data in preparation for exfiltration."
    ),
    "command_and_control": (
        "Command and control communications were established. {techniques} were observed "
        "across {count} events over {duration}. "
        "The attacker is communicating with external infrastructure to receive instructions."
    ),
    "exfiltration": (
        "Data exfiltration activity was detected across {count} events over {duration}. "
        "{techniques} were observed. Sensitive data may have left the environment "
        "during this phase of the attack."
    ),
    "impact": (
        "Impact-stage activity was observed — {count} events over {duration}. "
        "{techniques} detected. This phase may include ransomware deployment, "
        "data destruction, or service disruption."
    ),
}

DEFAULT_TEMPLATE = (
    "Activity was observed during the {display_name} phase across {count} events "
    "over {duration}. Techniques involved: {techniques}."
)


def _template_narration(phase_name: str, display_name: str,
                         events: list[dict], techniques: list[str]) -> str:
    count    = len(events)
    tech_str = ", ".join(techniques[:4]) if techniques else "unknown techniques"
    duration = _duration_str(events)
    template = PHASE_TEMPLATES.get(phase_name, DEFAULT_TEMPLATE)
    return template.format(
        techniques=tech_str,
        count=count,
        duration=duration,
        display_name=display_name,
    )


def _template_summary(name: str, phases: list[dict],
                       total: int, duration_min: float) -> str:
    phase_names = [p.get("display_name", p.get("phase_name", "")) for p in phases]
    all_tech: list[str] = []
    for p in phases:
        all_tech.extend(p.get("key_techniques", []))
    unique_tech = list(dict.fromkeys(all_tech))[:6]

    return (
        f"The investigation '{name}' captured {total} events across "
        f"{len(phases)} attack phases over approximately {duration_min:.0f} minutes. "
        f"The observed kill chain included: {', '.join(phase_names)}. "
        f"Key MITRE ATT&CK techniques identified: {', '.join(unique_tech) or 'see phase breakdown'}. "
        f"Ollama AI integration is pending — connect a local model for detailed natural-language analysis."
    )


def _duration_str(events: list[dict]) -> str:
    if not events:
        return "unknown duration"
    ts = [e["timestamp"] for e in events]
    diff_s = (max(ts) - min(ts)) / 1000
    if diff_s < 60:
        return f"{diff_s:.0f} seconds"
    if diff_s < 3600:
        return f"{diff_s/60:.1f} minutes"
    return f"{diff_s/3600:.1f} hours"
