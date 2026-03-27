import re
import base64
import io

def _solve_logic(file_bytes, log):
    from scapy.all import rdpcap, TCP
    import tempfile, os

    # Write to temp file for scapy
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pcap')
    tmp.write(file_bytes)
    tmp.close()
    
    try:
        packets = rdpcap(tmp.name)
    finally:
        os.unlink(tmp.name)

    rogue_cell_id = None
    for pkt in packets:
        raw = bytes(pkt)
        if b"UNAUTHORIZED-TEST-NETWORK" in raw:
            match = re.search(rb"CELLID=(\d+)", raw)
            if match:
                rogue_cell_id = match.group(1).decode()
                log.append(f"[+] Rogue Cell: {rogue_cell_id}")
                break

    if not rogue_cell_id:
        return None, "Could not identify rogue cell tower."

    compromised_imsi = None
    for pkt in packets:
        raw = bytes(pkt)
        if f"CELL:{rogue_cell_id}".encode() in raw:
            match = re.search(rb"IMSI:(\d+)", raw)
            if match:
                compromised_imsi = match.group(1).decode()
                log.append(f"[+] Compromised IMSI: {compromised_imsi}")
                break

    if not compromised_imsi:
        return None, "Could not identify compromised device."

    fragments = []
    for pkt in packets:
        if pkt.haslayer(TCP):
            payload = bytes(pkt[TCP].payload)
            if b"POST /upload" in payload and b"\r\n\r\n" in payload:
                data = payload.split(b"\r\n\r\n")[1].strip()
                if data:
                    fragments.append(data.decode(errors='ignore'))

    full_b64 = "".join(fragments)
    log.append(f"[*] Reassembled {len(full_b64)} chars of base64 payload.")

    try:
        encrypted_data = base64.b64decode(full_b64)
        for offset in range(len(compromised_imsi)):
            key = [ord(c) for c in compromised_imsi[offset:]]
            decrypted = "".join(chr(encrypted_data[i] ^ key[i % len(key)]) for i in range(len(encrypted_data)))
            if "picoCTF" in decrypted:
                flag = "picoCTF{" + decrypted.split("picoCTF{")[1].split("}")[0] + "}"
                return flag, None
        return None, "XOR decryption failed for all IMSI offsets."
    except Exception as e:
        return None, str(e)


def web_solve(params):
    files = params.get('files', [])
    if not files or files[0].filename == '':
        return {"success": False, "error": "Please upload a .pcap file."}
    
    log = []
    log.append("[*] Analyzing PCAP network capture...")
    
    try:
        file_bytes = files[0].read()
        log.append(f"[*] File loaded: {len(file_bytes)} bytes")
        flag, error = _solve_logic(file_bytes, log)
        if flag:
            log.append(f"[SUCCESS] Flag extracted!")
            return {"success": True, "flag": flag, "log": "\n".join(log)}
        else:
            return {"success": False, "error": error, "log": "\n".join(log)}
    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
        log = []
        flag, err = _solve_logic(data, log)
        print("\n".join(log))
        print("FLAG:", flag or err)
