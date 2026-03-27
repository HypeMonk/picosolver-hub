import requests
import re

def _find_wasm_url(base_url, html, log):
    """Deep search for wasm filenames regardless of JS obfuscation level."""
    # Standard candidates for Some Assembly Required 4
    for cand in ['ZoRd23o0wd', 'A7S8D9F0G1']:
        test_url = f"{base_url.rstrip('/')}/{cand}"
        try:
            r = requests.head(test_url, timeout=3)
            if r.status_code == 200:
                log.append(f"[*] Found binary via candidate check: {test_url}")
                return test_url
        except: pass
        
    # Strategy 1: Look for common fetch patterns
    match = re.search(r"fetch\(['\"]\.?/([A-Za-z0-9_-]+)['\"]", html)
    if match: return f"{base_url.rstrip('/')}/{match.group(1)}"
    
    # Strategy 2: Look for 8-20 character strings that are likely wasm filenames
    candidates = re.findall(r"['\"]([A-Za-z0-9]{8,15})['\"]", html)
    for c in list(set(candidates)):
        test_url = f"{base_url.rstrip('/')}/{c}"
        try:
            r = requests.head(test_url, timeout=3)
            if r.status_code == 200:
                ct = r.headers.get('content-type', '').lower()
                if 'wasm' in ct or 'application/octet-stream' in ct:
                    log.append(f"[*] Found binary candidate: {test_url}")
                    return test_url
        except: pass
    return None

def _decode_wasm(wasm_data, log):
    """Implementing the 'Official IITM-TDS' reversal script for Some Assembly Required 4."""
    # Start of data segment for ZoRd23o0wd
    sig = b"\x18\x6a\x7c\x61"
    start = wasm_data.find(sig)
    if start == -1: return None, "Could not find encrypted flag signature in binary."
    
    # 1. Extract the encrypted bytes (omit typical 2 trailing 0x00s)
    # The signature is 18 6a 7c 61... we take up to 41-43 bytes
    enc = list(wasm_data[start : start + 41])
    
    # 2. Undo byte-swapping
    unshuffled = list(enc)
    for i in range(0, len(unshuffled) - 1, 2):
        unshuffled[i], unshuffled[i+1] = unshuffled[i+1], unshuffled[i]
        
    # 3. Reverse XOR chain in FORWARD order (Forward pass)
    output = []
    for idx, char in enumerate(unshuffled):
        orig = char
        if idx % 3 == 0: orig ^= 7
        elif idx % 3 == 1: orig ^= 6
        else: orig ^= 5
        orig ^= (9 if idx % 2 == 0 else 8)
        orig ^= (idx % 10)
        # These are 'Look-Back' XORs on the ALREADY-UNSHUFFLED but STILL-ENCRYPTED data
        if idx > 2: orig ^= unshuffled[idx - 3]
        if idx > 0: orig ^= unshuffled[idx - 1]
        orig ^= 20
        output.append(orig & 0xFF)

    # Convert to string and find the flag
    final_str = "".join(chr(c) for c in output if 32 <= c <= 126)
    match = re.search(r'picoCTF\{[^}]+\}', final_str)
    if match: return match.group(0), None
    return final_str, f"Flag found but still scrambled: {final_str[:25]}"

def web_solve(params):
    base_url = params.get('url', '').rstrip('/')
    if not base_url: return {"success": False, "error": "URL required"}
    log = []
    try:
        root_url = base_url.rsplit('/', 1)[0] if '.html' in base_url else base_url
        log.append(f"[*] Analyzing page source for Wasm URL...")
        resp = requests.get(base_url, timeout=10)
        wasm_url = _find_wasm_url(root_url, resp.text, log)
        if not wasm_url: return {"success": False, "error": "Could not identify the binary filename in the source code.", "log": "\n".join(log)}

        log.append(f"[*] Retrieving {wasm_url}...")
        wasm_resp = requests.get(wasm_url, timeout=10)
        wasm_data = wasm_resp.content
        
        flag, err = _decode_wasm(wasm_data, log)
        if flag: return {"success": True, "flag": flag, "log": "\n".join(log) + "\n[SUCCESS] Flag found!"}
        else: return {"success": False, "error": err, "log": "\n".join(log)}
    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}
