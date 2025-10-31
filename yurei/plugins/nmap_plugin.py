# yurei/plugins/nmap_plugin.py
from rich.console import Console
import subprocess
import shutil
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, Union, List

console = Console()

# -----------------------
# Low-level helpers
# -----------------------

def _check_nmap() -> bool:
    if shutil.which("nmap") is None:
        console.print("[red]Error:[/red] nmap not found. Install it to use this plugin.")
        return False
    return True

def _is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False

IP_CIDR_RE = re.compile(r"\b(?:(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?)\b")
HOSTNAME_RE = re.compile(r"\b([a-z0-9\-]+\.[a-z]{2,})\b", re.I)
PORT_LIST_RE = re.compile(r"^(\d{1,5}(?:-\d{1,5})?(?:,\d{1,5})*)$")

def _normalize_target(target_like: Optional[str], default="127.0.0.1") -> str:
    """
    Accept either:
      - explicit IP/CIDR or hostname
      - 'None' -> default
      - a string which may include flags; extract first token
    """
    if not target_like:
        return default
    token = str(target_like).strip().split()[0]
    if IP_CIDR_RE.match(token) or HOSTNAME_RE.match(token) or re.match(r"^[\w\.\-:]+$", token):
        return token
    # fallback to original string (best-effort)
    return token or default

def _normalize_ports(ports_like: Optional[str]) -> Optional[str]:
    if not ports_like:
        return None
    ports_like = ports_like.strip()
    # Accept "top 100" as special handled in higher-level code
    if ports_like.lower().startswith("top"):
        return ports_like  # returned as-is (router should translate if desired)
    # If it looks like a list or range, return it
    if PORT_LIST_RE.match(ports_like):
        return ports_like
    # try to extract comma/dash containing token
    m = re.search(r"(\d{1,5}(?:-\d{1,5})?(?:,\d{1,5})*)", ports_like)
    if m:
        return m.group(1)
    return None

def _run_nmap(args: List[str], show_command: bool = False) -> Optional[subprocess.CompletedProcess]:
    if not _check_nmap():
        return None
    if show_command:
        console.print(f"[grey50][cmd][/grey50] {' '.join(args)}")
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        console.rule("[green]nmap output")
        # Prefer stdout; if empty show stderr
        out = result.stdout.strip() or result.stderr.strip()
        console.print(out)
        console.rule()
        return result
    except Exception as e:
        console.print(f"[red]Error running nmap:[/red] {e}")
        return None

# -----------------------
# High-level scan helpers (accept structured args)
# -----------------------

def host_discovery(target: Union[str, None] = None):
    target = _normalize_target(target)
    console.print(f"[cyan]Running host discovery (ping/ARP) on {target}...[/cyan]")
    return _run_nmap(["nmap", "-sn", target], show_command=True)

def ping_sweep(target: Union[str, None] = None):
    return host_discovery(target)

def top_ports_scan(target: str, top_n: int = 100):
    target = _normalize_target(target)
    console.print(f"[cyan]Scanning top {top_n} ports on {target}...[/cyan]")
    return _run_nmap(["nmap", f"--top-ports", str(top_n), target], show_command=True)

def full_tcp_scan(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running full TCP port scan on {target}...[/cyan]")
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] Full SYN scan (-sS) usually requires root. Falling back to connect scan (-sT).")
        return _run_nmap(["nmap", "-sT", "-p-", "-T3", target], show_command=True)
    return _run_nmap(["nmap", "-sS", "-p-", "-T4", target], show_command=True)

def service_version_scan(target: str, ports: Optional[str] = None, verbose: bool = False, aggressive: bool = False):
    target = _normalize_target(target)
    args = ["nmap"]
    if verbose:
        args.append("-v")
    if aggressive:
        args += ["-A"]
    else:
        # default: probe versions
        args += ["-sV"]
    if ports:
        args += ["-p", ports]
    args.append(target)
    console.print(f"[cyan]Running service/version detection on {target}...[/cyan]")
    return _run_nmap(args, show_command=True)

def os_detection(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running OS detection on {target}...[/cyan]")
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] OS detection works best as root and is noisy. Proceed only on authorized targets.")
    return _run_nmap(["nmap", "-O", target], show_command=True)

def udp_scan(target: str, ports: Optional[str] = None):
    target = _normalize_target(target)
    ports = ports or "1-1024"
    console.print(f"[cyan]Running UDP scan on {target} ports {ports}...[/cyan]")
    console.print("[yellow]Note:[/yellow] UDP scans are slower and less reliable; consider running as root for best results.")
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] Consider running as root/Administrator for best results.")
    return _run_nmap(["nmap", "-sU", "-p", ports, "-T3", target], show_command=True)

def vuln_script_scan(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running vulnerability scripts (nmap --script vuln) on {target}...[/cyan]")
    console.print("[red]WARNING:[/red] Vulnerability scripts can be intrusive and may impact target availability. Use only on authorized systems.")
    return _run_nmap(["nmap", "--script", "vuln", target], show_command=True)

def nse_default(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running default NSE scripts on {target}...[/cyan]")
    return _run_nmap(["nmap", "--script", "default", target], show_command=True)

def http_enum(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running HTTP enumeration against {target}...[/cyan]")
    return _run_nmap(["nmap", "-p", "80,443", "--script", "http-enum,http-title", target], show_command=True)

def smb_enum(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running SMB enumeration on {target} (port 445)...[/cyan]")
    console.print("[yellow]Warning:[/yellow] SMB enumeration can be noisy; run only on authorized hosts.")
    return _run_nmap(["nmap", "-p", "445", "--script", "smb-enum-shares,smb-vuln-ms17-010", target], show_command=True)

def traceroute_scan(target: str):
    target = _normalize_target(target)
    console.print(f"[cyan]Running traceroute to {target}...[/cyan]")
    return _run_nmap(["nmap", "--traceroute", target], show_command=True)

def save_output_scan(target: str, extra_flags: Optional[List[str]] = None):
    if not _check_nmap():
        return None
    target = _normalize_target(target)
    extra_flags = extra_flags or []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"scan_{target.replace('/', '_')}_{timestamp}"
    console.print(f"[cyan]Running scan on {target} and saving to {base}.*[/cyan]")
    args = ["nmap", "-oA", base] + extra_flags + [target]
    return _run_nmap(args, show_command=True)

# -----------------------
# Dispatcher: accept router payload
# -----------------------

def _extract_from_payload(intent_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the router payload to our internal shape:
      { target, ports, flags: { verbose, aggressive, udp, vuln, http, smb, save, top_n } }
    """
    slots = intent_payload.get("slots", {}) if intent_payload else {}
    target = slots.get("target") or slots.get("host") or None
    target = _normalize_target(target)
    ports = _normalize_ports(slots.get("ports"))
    flags = {
        "verbose": bool(slots.get("verbose")),
        "aggressive": bool(slots.get("aggressive")),
        "udp": bool(slots.get("udp")),
        "vuln": bool(slots.get("vuln")),
        "http": bool(slots.get("http")),
        "smb": bool(slots.get("smb")),
        "save": bool(slots.get("save")),
    }
    # support 'top' expressed as integer in slots
    top = slots.get("top") or None
    if isinstance(top, str) and top.isdigit():
        flags["top_n"] = int(top)
    elif isinstance(top, int):
        flags["top_n"] = top
    else:
        flags["top_n"] = None

    return {"target": target, "ports": ports, "flags": flags}

def handle_intent(intent_payload: Dict[str, Any], user_input: Optional[str] = None):
    """
    Main entrypoint for the router. Accepts the payload produced by parse_intent().
    Example payload:
      { "intent": "nmap_scan", "slots": {"target":"10.0.0.1", "ports":"22,80", "verbose":True } }
    """
    if not intent_payload or "intent" not in intent_payload:
        console.print("[red]Error:[/red] Invalid intent payload")
        return None

    intent = intent_payload["intent"]
    p = _extract_from_payload(intent_payload)
    target = p["target"]
    ports = p["ports"]
    flags = p["flags"]

    # Safety reminder
    if intent in ("vuln_scan",) or flags.get("vuln"):
        console.print("[red]Caution:[/red] You are about to run vulnerability checks. Ensure you have authorization.")

    # Dispatch
    if intent == "nmap_scan":
        # if UDP mode requested explicitly in slots, delegate to udp_scan
        if flags.get("udp"):
            return udp_scan(target, ports)
        # handle top-ports if requested
        if flags.get("top_n"):
            return top_ports_scan(target, flags["top_n"])
        # choose sS if root else sT; call service_version_scan wrapper
        return service_version_scan(target, ports=ports, verbose=flags["verbose"], aggressive=flags["aggressive"])

    if intent == "udp_scan":
        return udp_scan(target, ports)

    if intent == "http_enum" or flags.get("http"):
        return http_enum(target)

    if intent == "smb_enum" or flags.get("smb"):
        return smb_enum(target)

    if intent == "vuln_scan" or flags.get("vuln"):
        return vuln_script_scan(target)

    if intent == "ping":
        return host_discovery(target)

    if intent == "host_discovery":
        return host_discovery(target)

    if intent == "top_ports":
        n = flags.get("top_n") or 100
        return top_ports_scan(target, n)

    if intent == "full":
        return full_tcp_scan(target)

    if intent == "traceroute":
        return traceroute_scan(target)

    if intent == "save":
        extra = [] 
        return save_output_scan(target, extra)

    console.print(f"[yellow]Unknown intent in nmap_plugin:[/yellow] {intent}")
    return None


def run_scan(user_input: str):
    target = _normalize_target(user_input)
    return service_version_scan(target)

def verbose_scan(user_input: str):
    target = _normalize_target(user_input)
    return service_version_scan(target, verbose=True)

def udp_scan_legacy(user_input: str):
    parts = (user_input or "").split()
    target = parts[0] if parts else "127.0.0.1"
    ports = parts[1] if len(parts) > 1 else "1-1024"
    return udp_scan(target, ports)

# alias to minimize breakage
udp_scan = udp_scan if "udp_scan" not in globals() else globals()["udp_scan"]
