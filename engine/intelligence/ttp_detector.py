"""
TTP Detector — maps normalised Sysmon events to MITRE ATT&CK techniques.

Each signature returns:
  { code, name, tactic, confidence }

Suspicion score = weighted sum of matched technique confidences, capped at 100.
"""

from __future__ import annotations
import re

# ── Technique definitions ───────────────────────────────────────────────────────

TECHNIQUES = {
    "T1059.001": ("PowerShell",                     "execution"),
    "T1059.003": ("Windows Command Shell",           "execution"),
    "T1059.005": ("Visual Basic",                    "execution"),
    "T1059.007": ("JavaScript",                      "execution"),
    "T1047":     ("WMI Execution",                   "execution"),
    "T1053.005": ("Scheduled Task",                  "persistence"),
    "T1105":     ("Ingress Tool Transfer",            "command_and_control"),
    "T1218.005": ("Mshta",                           "defense_evasion"),
    "T1218.010": ("Regsvr32",                        "defense_evasion"),
    "T1218.011": ("Rundll32",                        "defense_evasion"),
    "T1218.007": ("Msiexec",                         "defense_evasion"),
    "T1548.002": ("UAC Bypass",                      "privilege_escalation"),
    "T1547.001": ("Registry Run Keys",               "persistence"),
    "T1543.003": ("Windows Service",                 "persistence"),
    "T1112":     ("Modify Registry",                 "defense_evasion"),
    "T1003.001": ("LSASS Memory Dump",               "credential_access"),
    "T1055":     ("Process Injection",               "defense_evasion"),
    "T1055.001": ("DLL Injection",                   "defense_evasion"),
    "T1055.002": ("PE Injection",                    "defense_evasion"),
    "T1082":     ("System Information Discovery",    "discovery"),
    "T1033":     ("System Owner Discovery",          "discovery"),
    "T1016":     ("Network Configuration Discovery", "discovery"),
    "T1057":     ("Process Discovery",               "discovery"),
    "T1087.001": ("Local Account Discovery",         "discovery"),
    "T1069.001": ("Local Group Discovery",           "discovery"),
    "T1136.001": ("Create Local Account",            "persistence"),
    "T1021.006": ("WinRM Lateral Movement",          "lateral_movement"),
    "T1021.002": ("SMB/Admin Shares",                "lateral_movement"),
    "T1027":     ("Obfuscated Content",              "defense_evasion"),
    "T1562.001": ("AMSI/AV Disable",                "defense_evasion"),
    "T1562.002": ("Disable Windows Firewall",        "defense_evasion"),
    "T1071.001": ("Web Protocol C2",                 "command_and_control"),
    "T1095":     ("Non-Standard Port C2",            "command_and_control"),
    "T1041":     ("Exfil over C2",                   "exfiltration"),
    "T1074.001": ("Data Staging",                    "collection"),
    "T1560":     ("Archive Collected Data",          "collection"),
    "T1566.001": ("Spearphishing Attachment",        "initial_access"),
    "T1190":     ("Exploit Public-Facing App",       "initial_access"),
    "T1078":     ("Valid Accounts",                  "initial_access"),
    "T1204.002": ("Malicious File Execution",        "execution"),
    "T1134.001": ("Token Impersonation",             "privilege_escalation"),
    "T1070.001": ("Clear Windows Event Logs",        "defense_evasion"),
    "T1490":     ("Inhibit System Recovery",         "impact"),
    "T1486":     ("Data Encrypted for Impact",       "impact"),
}

# High-value techniques — boost suspicion score
HIGH_VALUE = {
    "T1003.001", "T1055", "T1547.001", "T1105", "T1562.001",
    "T1070.001", "T1486", "T1490", "T1136.001"
}

# ── Signature rules ─────────────────────────────────────────────────────────────

# LOLBins that commonly indicate malicious use when spawned in unusual contexts
LOLBINS = {
    "certutil.exe",   "bitsadmin.exe",   "mshta.exe",       "regsvr32.exe",
    "rundll32.exe",   "wscript.exe",     "cscript.exe",     "msiexec.exe",
    "wmic.exe",       "powershell.exe",  "pwsh.exe",        "cmd.exe",
    "schtasks.exe",   "at.exe",          "sc.exe",          "reg.exe",
    "net.exe",        "net1.exe",        "nltest.exe",      "whoami.exe",
    "systeminfo.exe", "ipconfig.exe",    "netstat.exe",     "tasklist.exe",
    "arp.exe",        "route.exe",       "xcopy.exe",       "robocopy.exe",
    "forfiles.exe",   "pcalua.exe",      "eventvwr.exe",    "fodhelper.exe",
    "sdclt.exe",      "cmstp.exe",
}

# Office apps that spawn shells = macro/phishing initial access
OFFICE_APPS = {
    "winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe",
    "onenote.exe", "mspub.exe", "visio.exe", "access.exe"
}

# Non-standard C2 ports
C2_PORTS = {4444, 4445, 5555, 6666, 7777, 8888, 9001, 9030, 1337, 31337,
            1234, 2222, 3333, 12345, 8443, 8080, 4000, 5000}


def detect_ttps(event: dict) -> list[dict]:
    """
    Returns list of matched TTPs: [{code, name, tactic, confidence}, ...]
    """
    etype = event.get("event_type", "")
    ttps = []

    if etype == "process_create":
        ttps = _check_process_create(event)
    elif etype == "network_connect":
        ttps = _check_network_connect(event)
    elif etype in ("registry_set", "registry_create", "registry_rename"):
        ttps = _check_registry(event)
    elif etype == "process_access":
        ttps = _check_process_access(event)
    elif etype == "dns_query":
        ttps = _check_dns(event)
    elif etype == "create_remote_thread":
        ttps = _check_remote_thread(event)
    elif etype == "process_tamper":
        ttps = [_ttp("T1055", 90)]
    elif etype in ("file_delete", "file_delete_detected"):
        ttps = _check_file_delete(event)

    return ttps


def score_event(event: dict, ttps: list[dict]) -> float:
    """0–100 suspicion score."""
    if not ttps:
        return 5.0  # baseline noise

    best = max(t["confidence"] for t in ttps)
    bonus = sum(15 for t in ttps if t["code"] in HIGH_VALUE)
    multi_bonus = min(len(ttps) * 5, 20)
    return min(best + bonus + multi_bonus, 100.0)


# ── Per-event-type checkers ─────────────────────────────────────────────────────

def _check_process_create(ev: dict) -> list[dict]:
    ttps = []
    img  = (ev.get("image_name") or "").lower()
    cmd  = (ev.get("cmd") or "").lower()
    par  = (ev.get("parent_name") or "").lower()

    # PowerShell suspicious invocations
    if img in ("powershell.exe", "pwsh.exe"):
        if any(x in cmd for x in ("-enc", "-encodedcommand", "iex ", "invoke-expression",
                                   "downloadstring", "webclient", "invoke-webrequest",
                                   "start-bitstransfer", "[convert]::frombase64")):
            ttps.append(_ttp("T1059.001", 90))
            if "-enc" in cmd or "-encodedcommand" in cmd:
                ttps.append(_ttp("T1027", 75))
        else:
            ttps.append(_ttp("T1059.001", 40))

        # AMSI bypass patterns
        if any(x in cmd for x in ("amsiutils", "amsi.dll", "amsicontext",
                                   "amsiscanstring", "[ref].assembly", "set-mppreference")):
            ttps.append(_ttp("T1562.001", 95))

    # Office app spawning a shell = macro execution
    if par in OFFICE_APPS and img in ("cmd.exe", "powershell.exe", "pwsh.exe",
                                       "wscript.exe", "cscript.exe", "mshta.exe"):
        ttps.append(_ttp("T1566.001", 85))
        ttps.append(_ttp("T1204.002", 80))

    # LOLBin tool transfer
    if img in ("certutil.exe", "bitsadmin.exe"):
        if any(x in cmd for x in ("-urlcache", "-f", "transfer", "/transfer")):
            ttps.append(_ttp("T1105", 90))
        else:
            ttps.append(_ttp("T1105", 35))

    # WMI
    if img == "wmic.exe":
        ttps.append(_ttp("T1047", 60))
        if "process call create" in cmd:
            ttps.append(_ttp("T1047", 85))

    # Scheduled tasks
    if img == "schtasks.exe":
        if any(x in cmd for x in ("/create", "-create")):
            ttps.append(_ttp("T1053.005", 85))

    # LOLBin proxies
    if img == "mshta.exe":
        ttps.append(_ttp("T1218.005", 80))
    if img == "regsvr32.exe" and any(x in cmd for x in ("/s", "/u", "scrobj")):
        ttps.append(_ttp("T1218.010", 85))
    if img == "rundll32.exe":
        ttps.append(_ttp("T1218.011", 60))

    # UAC bypass candidates
    if img in ("fodhelper.exe", "eventvwr.exe", "sdclt.exe", "cmstp.exe"):
        ttps.append(_ttp("T1548.002", 85))

    # Discovery tools
    if img == "whoami.exe":
        ttps.append(_ttp("T1033", 50))
    if img == "systeminfo.exe":
        ttps.append(_ttp("T1082", 50))
    if img in ("ipconfig.exe", "arp.exe", "route.exe", "netstat.exe"):
        ttps.append(_ttp("T1016", 40))
    if img == "tasklist.exe":
        ttps.append(_ttp("T1057", 40))

    # Account enumeration / creation
    if img in ("net.exe", "net1.exe"):
        if "user /add" in cmd or "user/add" in cmd:
            ttps.append(_ttp("T1136.001", 90))
        elif "user" in cmd or "localgroup" in cmd:
            ttps.append(_ttp("T1087.001", 45))
            ttps.append(_ttp("T1069.001", 45))

    # nltest = domain reconnaissance
    if img == "nltest.exe":
        ttps.append(_ttp("T1087.001", 60))

    # Firewall disable
    if img == "netsh.exe" and any(x in cmd for x in ("firewall", "advfirewall")):
        if "off" in cmd or "disable" in cmd:
            ttps.append(_ttp("T1562.002", 85))

    # Event log clearing
    if img == "wevtutil.exe" and any(x in cmd for x in ("cl ", "clear-log")):
        ttps.append(_ttp("T1070.001", 95))

    # Shadow copy deletion (ransomware pre-encryption)
    if any(x in cmd for x in ("vssadmin delete shadows", "wbadmin delete",
                               "bcdedit /set", "diskshadow")):
        ttps.append(_ttp("T1490", 95))

    # Archive / staging
    if img in ("7z.exe", "7za.exe", "rar.exe", "winrar.exe") and any(
            x in cmd for x in ("a ", "-a", "add")):
        ttps.append(_ttp("T1560", 70))
    if img in ("xcopy.exe", "robocopy.exe"):
        ttps.append(_ttp("T1074.001", 55))

    # VBScript / JScript
    if img in ("wscript.exe", "cscript.exe"):
        ttps.append(_ttp("T1059.005", 65))

    return ttps


def _check_network_connect(ev: dict) -> list[dict]:
    ttps = []
    img   = (ev.get("image_name") or "").lower()
    port  = int(ev.get("dest_port") or 0)
    dest  = ev.get("dest_ip", "") or ""

    # LOLBin making outbound connection
    if img in LOLBINS:
        if port in (80, 443, 8080, 8443):
            ttps.append(_ttp("T1071.001", 75))
        else:
            ttps.append(_ttp("T1071.001", 50))

    # Non-standard C2 ports
    if port in C2_PORTS:
        ttps.append(_ttp("T1095", 80))

    # Private range to private range = lateral movement candidate
    if _is_private(dest) and img in LOLBINS:
        ttps.append(_ttp("T1021.002", 60))

    return ttps


def _check_registry(ev: dict) -> list[dict]:
    ttps = []
    key  = (ev.get("target_object") or "").lower()

    if re.search(r"\\(software\\microsoft\\windows\\currentversion\\run|runonce)\\", key):
        ttps.append(_ttp("T1547.001", 90))

    if re.search(r"\\system\\currentcontrolset\\services\\", key):
        ttps.append(_ttp("T1543.003", 75))

    if re.search(r"\\winlogon|\\appinit_dlls|\\image file execution options", key):
        ttps.append(_ttp("T1112", 70))

    if re.search(r"\\policies\\.*\\disableregistrytools|\\limitblankpassworduse", key):
        ttps.append(_ttp("T1112", 65))

    return ttps


def _check_process_access(ev: dict) -> list[dict]:
    ttps = []
    target = (ev.get("target_name") or "").lower()
    access = (ev.get("granted_access") or "").lower()

    if target == "lsass.exe":
        # Any access to lsass is suspicious; high access rights = credential dump
        confidence = 95 if access in ("0x1fffff", "0x1010", "0x1410", "0x40") else 75
        ttps.append(_ttp("T1003.001", confidence))

    # Generic process injection indicators
    # PROCESS_VM_WRITE | PROCESS_CREATE_THREAD = classic injection
    if access in ("0x1fffff", "0x1f0fff"):
        ttps.append(_ttp("T1055", 80))
    elif "vm_write" in (ev.get("call_trace") or "").lower():
        ttps.append(_ttp("T1055.001", 75))

    return ttps


def _check_dns(ev: dict) -> list[dict]:
    ttps = []
    img   = (ev.get("image_name") or "").lower()
    query = (ev.get("query_name") or "").lower()

    # Long subdomain = possible DNS tunnelling
    parts = query.split(".")
    if parts and len(parts[0]) > 40:
        ttps.append(_ttp("T1041", 70))

    # LOLBin making DNS query
    if img in LOLBINS and img not in ("cmd.exe",):
        ttps.append(_ttp("T1071.001", 50))

    return ttps


def _check_remote_thread(ev: dict) -> list[dict]:
    ttps = []
    src = (ev.get("source_name") or "").lower()
    tgt = (ev.get("target_name") or "").lower()

    ttps.append(_ttp("T1055", 85))

    # Classic Cobalt Strike / shellcode loader pattern
    if tgt in ("explorer.exe", "svchost.exe", "spoolsv.exe"):
        ttps.append(_ttp("T1055.002", 90))

    return ttps


def _check_file_delete(ev: dict) -> list[dict]:
    # Ransomware deletes originals post-encryption; also log clearing
    return [_ttp("T1070.001", 55)]


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _ttp(code: str, confidence: int) -> dict:
    name, tactic = TECHNIQUES.get(code, ("Unknown", "unknown"))
    return {"code": code, "name": name, "tactic": tactic, "confidence": confidence}


def _is_private(ip: str) -> bool:
    return (ip.startswith("10.") or ip.startswith("192.168.") or
            ip.startswith("172.16.") or ip.startswith("172.17."))
