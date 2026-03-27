import wave
import struct
import sys
import os
import io

def _decode_wav(wav_bytes, log):
    with wave.open(io.BytesIO(wav_bytes), 'rb') as w:
        n_frames = w.getnframes()
        width = w.getsampwidth()
        raw = w.readframes(n_frames)
        if width != 2:
            return None, f"Unsupported bit depth: {width}"
        samples = struct.unpack(f'<{n_frames}h', raw)

    rounded = [abs(s) // 100 for s in samples]
    unique_levels = sorted(list(set(rounded)))
    log.append(f"[*] {len(unique_levels)} discrete amplitude levels found.")

    if len(unique_levels) != 16:
        log.append(f"[!] Warning: Expected 16 hex levels, found {len(unique_levels)}.")

    hex_chars = []
    for val in rounded:
        try:
            hex_chars.append(format(unique_levels.index(val), 'x'))
        except ValueError:
            pass

    hex_str = "".join(hex_chars)
    try:
        decoded = bytes.fromhex(hex_str).decode('utf-8', errors='ignore')
        if "picoCTF" in decoded:
            flag = "picoCTF{" + decoded.split("picoCTF{")[1].split("}")[0] + "}"
            return flag, None
        else:
            return None, "Flag pattern not found in decoded audio data."
    except Exception as e:
        return None, str(e)


def web_solve(params):
    files = params.get('files', [])
    if not files or files[0].filename == '':
        return {"success": False, "error": "Please upload the .wav audio file."}
    
    log = []
    log.append("[*] Analyzing audio amplitude levels...")
    
    try:
        wav_bytes = files[0].read()
        log.append(f"[*] File loaded: {len(wav_bytes)} bytes")
        flag, error = _decode_wav(wav_bytes, log)
        if flag:
            log.append("[SUCCESS] Flag recovered from audio amplitudes!")
            return {"success": True, "flag": flag, "log": "\n".join(log)}
        else:
            return {"success": False, "error": error, "log": "\n".join(log)}
    except Exception as e:
        return {"success": False, "error": str(e), "log": "\n".join(log)}


if __name__ == "__main__":
    path = r"C:\Users\HP\Project-2\questions-data\main.wav"
    if len(sys.argv) > 1: path = sys.argv[1]
    with open(path, 'rb') as f:
        data = f.read()
    log = []
    flag, err = _decode_wav(data, log)
    print("\n".join(log))
    print("FLAG:", flag or err)
