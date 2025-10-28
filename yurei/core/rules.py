def parse_intent(user_input: str) -> str:
    #Return an intent string based on simple keyword rules.
    lower = user_input.lower()

    if "scan" in lower or "nmap" in lower:
        return "nmap_scan"
    elif "ping" in lower:
        return "ping"
    else:
        return "unknown"