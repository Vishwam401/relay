"""Spawn src.worker in a new process group, wait for an anchor line, send CTRL_BREAK_EVENT.

Usage:
  python -u harness_sigbreak.py "<anchor regex>" <delay_seconds> <log path>
Log format matches the PowerShell wrapper: 'yyyy-MM-dd HH:mm:ss.fff|<line>' in UTC,
so Get-LogEvent works across the worker log, the reaper log, and this one.
"""
import os, re, signal, subprocess, sys, threading, time
from datetime import datetime, timezone

anchor = re.compile(sys.argv[1])
delay = float(sys.argv[2])
log = open(sys.argv[3], "w", encoding="utf-8", buffering=1)

def stamp(text):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}"
    line = f"{ts}|{text}"
    log.write(line + "\n")
    print(line, flush=True)

proc = subprocess.Popen(
    [sys.executable, "-u", "-m", "src.worker"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
)
stamp(f"[harness] spawned group_leader_pid={proc.pid} delay={delay}")

hit = threading.Event()

def pump():
    for raw in proc.stdout:
        text = raw.rstrip("\r\n")
        stamp(text)
        if not hit.is_set() and anchor.search(text):
            stamp(f"[harness] ANCHOR matched")
            hit.set()

threading.Thread(target=pump, daemon=True).start()

if not hit.wait(timeout=180):
    stamp("[harness] ANCHOR never matched; aborting without signal")
    proc.kill()
    sys.exit(2)

time.sleep(delay)
os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
stamp(f"[harness] CTRL_BREAK_EVENT sent to group {proc.pid}")

t0 = time.perf_counter()
rc = proc.wait()
stamp(f"[harness] child exited rc={rc} signal_to_exit={time.perf_counter() - t0:.3f}s")
time.sleep(0.5)
log.close()
