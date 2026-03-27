from flask import Flask, render_template, request, jsonify
import importlib
import uuid
import threading
import time
import os

app = Flask(__name__)

# CHALLENGE DATABASE
CHALLENGES = [
    {"id": "crack_the_gate_1", "name": "Crack the Gate 1", "type": "web", "desc": "Bypass validation gates via dynamic URL payloads."},
    {"id": "power_cookie", "name": "Power Cookie", "type": "web", "desc": "Manipulate session cookies to gain admin access."},
    {"id": "rogue_tower", "name": "Rogue Tower", "type": "file", "desc": "Analyze PCAP traffic to recover hidden flags."},
    {"id": "ssti2", "name": "SSTI2", "type": "web", "desc": "Server-side template injection with underscore bypass."},
    {"id": "solve_q5", "name": "Investigative Reversing 4", "type": "multi_file", "desc": "LSB recovery from multiple encoded BMP images."},
    {"id": "js_kiddie_solver", "name": "Java Script Kiddie", "type": "web", "desc": "Reconstruct QR codes using mathematical CRC validation."},
    {"id": "m00nwalk2_solver", "name": "m00nwalk2", "type": "static", "desc": "Recover flag from universal SSTV audio mapping."},
    {"id": "sidechannel_solver", "name": "SideChannel", "type": "timing", "desc": "Iterative timing attack to recover 8-digit PINs."},
    {"id": "q9_solver", "name": "Some Assembly Required 4", "type": "web", "desc": "De-obfuscating and reversing Wasm logic."},
    {"id": "surfing_waves_solver", "name": "Surfing the Waves", "type": "file", "desc": "Amplitude-to-hex mapping from WAV audio files."}
]

TASKS = {}

def run_solver_async(task_id, module_name, params):
    try:
        solver_module = importlib.import_module(f'solvers.{module_name}')
        params['task_id'] = task_id
        params['TASKS_REF'] = TASKS 
        result = solver_module.web_solve(params)
        if 'log' in result:
             TASKS[task_id]['log'] = result['log']
        TASKS[task_id]['result'] = result
        TASKS[task_id]['status'] = 'completed'
    except Exception as e:
        TASKS[task_id]['status'] = 'failed'
        TASKS[task_id]['error'] = str(e)

@app.route('/')
def home():
    return render_template('dashboard.html', challenges=CHALLENGES)

@app.route('/solve', methods=['POST'])
def solve():
    data = request.form
    # Note: Frontend must send 'id' or we fallback to 'challenge_id'
    cid = data.get('id') or data.get('challenge_id')
    
    if not cid:
        return jsonify({"success": False, "error": "No challenge ID provided"})

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        'status': 'running',
        'id': cid,
        'log': "[*] Handshake successful. Initializing solver module...",
        'result': None
    }
    
    params = {'url': data.get('url'), 'files': request.files.getlist('files')}
    thread = threading.Thread(target=run_solver_async, args=(task_id, cid, params))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "task_id": task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404
    return jsonify(task)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
