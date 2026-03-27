import os
import io

def _solve_bmp_bytes(bmp_files_bytes, log):
    """
    bmp_files_bytes: list of (filename, bytes) tuples, sorted by filename.
    Extracts LSB-encoded flag characters from 5 BMP files.
    """
    # Files must be in order 5 -> 1 (as per the original binary logic)
    # Sort by filename descending (Item05 first)
    bmp_files_bytes.sort(key=lambda x: x[0], reverse=True)

    log.append(f"[*] Processing {len(bmp_files_bytes)} BMP files...")
    bin_str = ""

    for fname, raw in bmp_files_bytes:
        log.append(f"[*] Reading {fname}...")
        f = io.BytesIO(raw)
        f.seek(2019)
        for j in range(50):
            if j % 5 == 0:
                bits = []
                for _ in range(8):
                    byte = f.read(1)
                    if not byte: break
                    bits.append(byte[0] & 1)
                if len(bits) == 8:
                    char_code = 0
                    for idx, bit in enumerate(bits):
                        char_code |= (bit << idx)
                    bin_str += chr(char_code)
            else:
                f.read(1)

    return bin_str


def web_solve(params):
    files = params.get('files', [])
    if not files or files[0].filename == '':
        return {"success": False, "error": "Please upload the 5 BMP files."}
    
    log = []
    log.append(f"[*] Received {len(files)} BMP file(s).")
    
    try:
        bmp_data = [(f.filename, f.read()) for f in files]
        result = _solve_bmp_bytes(bmp_data, log)
        
        if "picoCTF" in result:
            flag = "picoCTF{" + result.split("picoCTF{")[1].split("}")[0] + "}"
            log.append("[SUCCESS] Flag reconstructed from LSB data!")
            return {"success": True, "flag": flag, "log": "\n".join(log)}
        else:
            log.append(f"[*] Recovered text: {result}")
            return {"success": False, "error": "Flag pattern not found in decoded data. Check file order.", "log": "\n".join(log)}
    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}


if __name__ == "__main__":
    import sys
    data_dir = r"C:\Users\HP\Project-2\questions-data\q5"
    bmp_data = []
    for fname in os.listdir(data_dir):
        if fname.endswith('.bmp'):
            with open(os.path.join(data_dir, fname), 'rb') as f:
                bmp_data.append((fname, f.read()))
    log = []
    print(_solve_bmp_bytes(bmp_data, log))
