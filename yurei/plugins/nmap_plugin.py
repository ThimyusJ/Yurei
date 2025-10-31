from rich.console import Console
import subprocess
import shutil
import os
import re
from datetime import datetime

console = Console()

def _check_nmap():
    if shutil.which("nmap") is None:
        console.print("[red]Error:[/red] nmap not found. Install it to use this plugin.")
        return False
    return True

def _is_root():
    # Works on Unix-like systems; returns False on Windows
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False

def _parse_target(user_input: str, default="127.0.0.1"):
    """
    Simple target extraction:
    - if input contains an IP, CIDR, or hostname, return that first token
    - otherwise return default
    """
    if not user_input:
        return default
    token = user_input.strip().split()[0]
    # crude checks for ip/cidr/hostname
    if re.match(r"^[\w\.\-:/]+$", token):
        return token
    return default

def _run_nmap(args: list, show_command: bool = False):
    """
    Run nmap with basic error handling and print results to console.
    """
    if not _check_nmap():
        return None
    if show_command:
        console.print(f"[grey50][cmd][/grey50] {' '.join(args)}")
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        console.rule("[green]nmap output")
        console.print(result.stdout or result.stderr)
        console.rule()
        return result
    except Exception as e:
        console.print(f"[red]Error running nmap:[/red] {e}")
        return None

# ------------ Recon helpers ------------

def host_discovery(user_input: str):
    """
    Simple host discovery (ping/ARP sweep). Good for quickly listing live hosts in a subnet.
    Example user_input: "192.168.1.0/24"
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running host discovery (ping/ARP) on {target}...[/cyan]")
    _run_nmap(["nmap", "-sn", target], show_command=True)

def ping_sweep(user_input: str):
    """
    Alias for host_discovery; kept for CLI familiarity.
    """
    host_discovery(user_input)

def top_ports_scan(user_input: str):
    """
    Scan the top N common ports (default 100).
    Example: "192.168.1.0/24 200" to scan top 200 ports
    """
    parts = user_input.split()
    target = parts[0] if parts else "127.0.0.1"
    top_n = parts[1] if len(parts) > 1 else "100"
    console.print(f"[cyan]Scanning top {top_n} ports on {target}...[/cyan]")
    _run_nmap(["nmap", f"--top-ports", top_n, target], show_command=True)

def full_tcp_scan(user_input: str):
    """
    Full TCP port scan (-p-). SYN scan requires root on Unix.
    Example: "10.0.0.5"
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running full TCP port scan on {target}...[/cyan]")
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] Full SYN scan (-sS) usually requires root. Falling back to connect scan (-sT).")
        _run_nmap(["nmap", "-sT", "-p-", "-T3", target], show_command=True)
    else:
        _run_nmap(["nmap", "-sS", "-p-", "-T4", target], show_command=True)

def service_version_scan(user_input: str):
    """
    Version/service detection on the target. (nmap -sV)
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running service/version detection on {target}...[/cyan]")
    _run_nmap(["nmap", "-sV", target], show_command=True)

def os_detection(user_input: str):
    """
    OS detection (-O). Requires elevated privileges and can be noisy.
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running OS detection on {target}...[/cyan]")
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] OS detection works best as root and is noisy. Proceed only on authorized targets.")
    _run_nmap(["nmap", "-O", target], show_command=True)

def udp_scan(user_input: str):
    """
    UDP scan on common ports by default. Full UDP (-p-) is very slow.
    Example inputs:
      - "10.0.0.5" => scans common UDP ports 1-1024
      - "10.0.0.0/24 1-65535" => scans all UDP ports (may take very long)
    """
    parts = user_input.split()
    target = parts[0] if parts else "127.0.0.1"
    ports = parts[1] if len(parts) > 1 else "1-1024"
    console.print(f"[cyan]Running UDP scan on {target} ports {ports}...[/cyan]")
    console.print("[yellow]Note:[/yellow] UDP scans are slower and less reliable; consider running from a machine with stable network connectivity.")
    # UDP scans often need root to send raw packets efficiently
    if not _is_root():
        console.print("[yellow]Warning:[/yellow] Consider running as root/Administrator for best results.")
    _run_nmap(["nmap", "-sU", "-p", ports, "-T3", target], show_command=True)

def vuln_script_scan(user_input: str):
    """
    Run Nmap's 'vuln' script category. Can be intrusive—use only with consent.
    Example: "10.0.0.5"
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running vulnerability scripts (nmap --script vuln) on {target}...[/cyan]")
    console.print("[red]WARNING:[/red] Vulnerability scripts can be intrusive and may impact target availability. Use only on authorized systems.")
    _run_nmap(["nmap", "--script", "vuln", target], show_command=True)

def nse_default(user_input: str):
    """
    Run the default NSE script set (safe by default).
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running default NSE scripts on {target}...[/cyan]")
    _run_nmap(["nmap", "--script", "default", target], show_command=True)

def http_enum(user_input: str):
    """
    Enumerate HTTP services and common files/endpoints on ports 80/443.
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running HTTP enumeration against {target}...[/cyan]")
    _run_nmap(["nmap", "-p", "80,443", "--script", "http-enum,http-title", target], show_command=True)

def smb_enum(user_input: str):
    """
    SMB enumeration (shares, MS17-010 checks). Target: host or IP. Use only with permission.
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running SMB enumeration on {target} (port 445)...[/cyan]")
    console.print("[yellow]Warning:[/yellow] SMB enumeration can be noisy; run only on authorized hosts.")
    _run_nmap(["nmap", "-p", "445", "--script", "smb-enum-shares,smb-vuln-ms17-010", target], show_command=True)

def traceroute_scan(user_input: str):
    """
    Run nmap with traceroute to map the network path.
    """
    target = _parse_target(user_input)
    console.print(f"[cyan]Running traceroute to {target}...[/cyan]")
    _run_nmap(["nmap", "--traceroute", target], show_command=True)

def save_output_scan(user_input: str):
    """
    Run a scan and save output to files with a timestamped base name.
    Example: "10.0.0.5 -A"
    The function will append -A or other flags as provided by the user after the target.
    """
    if not _check_nmap():
        return
    parts = user_input.split()
    if not parts:
        console.print("[red]Error:[/red] provide target and optional flags. e.g. '10.0.0.5 -A'")
        return
    target = parts[0]
    extra_flags = parts[1:]  # pass-through flags
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"scan_{target.replace('/', '_')}_{timestamp}"
    console.print(f"[cyan]Running scan on {target} and saving to {base}.*[/cyan]")
    args = ["nmap", "-oA", base] + extra_flags + [target]
    _run_nmap(args, show_command=True)

# Example usage mapping - adapt to your CLI dispatcher
# map "hostdiscovery" -> host_discovery(...)
# map "top" -> top_ports_scan(...)
# map "full" -> full_tcp_scan(...)
# map "udp" -> udp_scan(...)
# map "http" -> http_enum(...)
# map "smb" -> smb_enum(...)
# map "vuln" -> vuln_script_scan(...)
# map "save" -> save_output_scan(...)
