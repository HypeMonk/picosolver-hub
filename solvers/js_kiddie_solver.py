import itertools
import requests
import base64
import io
import zlib
import struct
from PIL import Image
import cv2
import numpy as np
import io

LEN = 16
PNG_HEADER = b"\x89PNG\x0d\x0a\x1a\x0a"

def fetch_bytes(base_url):
    resp = requests.get(f"{base_url.rstrip('/')}/bytes", timeout=15)
    resp.raise_for_status()
    return [int(x) for x in resp.text.strip().split()]

def assemble_png(key, byte_list):
    shifters = [ord(c) - 48 for c in key]
    rows = len(byte_list) // LEN
    result = bytearray(len(byte_list))
    for i in range(LEN):
        sh = shifters[i]
        for j in range(rows):
            src = (((j + sh) * LEN) % len(byte_list)) + i
            dst = (j * LEN) + i
            result[dst] = byte_list[src]
    while result and result[-1] == 0:
        result.pop()
    return bytes(result)

def is_valid_png_mathematically(png_data):
    """Deep validation using CRCs of standard chunks."""
    if not png_data.startswith(PNG_HEADER): return False
    
    # Check IHDR Chunk (starts at offset 8)
    try:
        ihdr_len = struct.unpack(">I", png_data[8:12])[0]
        ihdr_type = png_data[12:16]
        ihdr_data = png_data[16:16+ihdr_len]
        ihdr_crc = struct.unpack(">I", png_data[16+ihdr_len:20+ihdr_len])[0]
        if zlib.crc32(ihdr_type + ihdr_data) & 0xffffffff != ihdr_crc:
            return False
            
        # Optional: verify IDAT exists
        if b"IDAT" not in png_data: return False
        
        # Verify IEND CRC at the very end
        if png_data[-4:] != b"":
            iend_type_data = b"IEND"
            iend_crc = struct.unpack(">I", png_data[-4:])[0]
            if zlib.crc32(iend_type_data) & 0xffffffff != iend_crc:
                return False
                
        return True
    except:
        return False

def web_solve(params):
    base_url = params.get('url')
    if not base_url: return {"success": False, "error": "URL required"}
    
    log = []
    log.append(f"[*] Attacking: {base_url}")
    try:
        byte_list = fetch_bytes(base_url)
        num_rows = len(byte_list) // LEN
        
        # 1. Prune candidates for each column (Header + IHDR markers)
        possibilities = []
        for col in range(LEN):
            cands = []
            target = None
            if col < 8: target = PNG_HEADER[col]
            elif col == 12: target = 0x49  # 'I' in IHDR
            elif col == 13: target = 0x48  # 'H' in IHDR
            
            if target is not None:
                for s in range(10): 
                    if byte_list[s*LEN + col] == target: cands.append(s)
            else:
                cands = list(range(10))
            
            if not cands and col in [0,1,2,3,4,5,6,7,12,13]:
                return {"success": False, "error": f"Column {col} has no valid start bytes."}
            possibilities.append(cands or [0])

        log.append("[*] Solving key via Scanning Filter (this may take a moment)...")
        
        # 2. Brute force with Mathematical CRC check + QR scanning filter
        for combo in itertools.product(*possibilities):
            key = "".join(str(s) for s in combo)
            png = assemble_png(key, byte_list)
            
            # TURBO FILTER: Fast mathematical validation first!
            if not is_valid_png_mathematically(png): continue
            
            # Only if the Math passes, we use the heavy OpenCV Eye
            try:
                # Decrypt raw bytes to OpenCV image
                nparr = np.frombuffer(png, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None: continue
                
                # Use OpenCV's built-in QR detector
                detector = cv2.QRCodeDetector()
                data, _, _ = detector.detectAndDecode(img)
                if data:
                    log.append(f"[SUCCESS] Mathematical & Scanner Match: {key}")
                    img_b64 = base64.b64encode(png).decode('utf-8')
                    return {
                        "success": True, 
                        "flag": data,
                        "qr_data": f"data:image/png;base64,{img_b64}",
                        "log": "\n".join(log)
                    }
            except: pass
                
        return {"success": False, "error": "Scanning failed to find a valid QR code.", "log": "\n".join(log)}

    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}
