import datetime
import os
import signal
import subprocess
import sys
import time

SUPERVISOR_LOG = "logs/w5d2_step4_supervisor.log"


def log_event(msg: str) -> None:
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    line = f"[{now_str}] [supervisor] {msg}"
    print(line, flush=True)
    with open(SUPERVISOR_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


class SupervisedProcess:
    def __init__(self, name: str, cmd: list[str], stdout_path: str, stderr_path: str):
        self.name = name
        self.cmd = cmd
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.proc: subprocess.Popen | None = None
        self.restarts = 0
        self.last_start_time = 0.0
        self.backoff = 1.0

    def start(self) -> None:
        out_f = open(self.stdout_path, "a", encoding="utf-8")
        err_f = open(self.stderr_path, "a", encoding="utf-8")
        self.last_start_time = time.monotonic()
        self.proc = subprocess.Popen(
            self.cmd,
            stdout=out_f,
            stderr=err_f,
            env=os.environ.copy(),
        )
        log_event(
            f"Started {self.name} (PID: {self.proc.pid}, restart_count: {self.restarts})"
        )

    def poll_and_restart(self) -> None:
        if self.proc is None:
            self.start()
            return

        exit_code = self.proc.poll()
        if exit_code is not None:
            uptime = time.monotonic() - self.last_start_time
            self.restarts += 1
            log_event(
                f"{self.name} (PID: {self.proc.pid}) EXITED with code {exit_code} after {uptime:.2f}s uptime. Total restarts: {self.restarts}"
            )

            # Crash-loop backoff calculation
            if uptime < 5.0:
                self.backoff = min(self.backoff * 2.0, 5.0)
            else:
                self.backoff = 1.0

            log_event(
                f"Applying crash-loop backoff: sleeping {self.backoff:.2f}s before restarting {self.name}..."
            )
            time.sleep(self.backoff)
            self.start()

    def terminate(self) -> None:
        if self.proc and self.proc.poll() is None:
            log_event(f"Terminating {self.name} (PID: {self.proc.pid})...")
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3.0)
            except Exception:
                self.proc.kill()


SHUTDOWN = False


def sig_handler(sig, frame):
    global SHUTDOWN
    SHUTDOWN = True
    log_event(f"Received signal {sig}. Initiating shutdown...")


def main():
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, sig_handler)

    os.makedirs("logs", exist_ok=True)
    log_event("Supervisor starting...")

    # Supervise worker and reaper
    processes = [
        SupervisedProcess(
            "worker",
            [sys.executable, "-m", "src.worker"],
            "logs/w5d2_step4_worker.stdout.log",
            "logs/w5d2_step4_worker.stderr.log",
        ),
        SupervisedProcess(
            "reaper",
            [sys.executable, "-m", "src.reaper"],
            "logs/w5d2_step4_reaper.stdout.log",
            "logs/w5d2_step4_reaper.stderr.log",
        ),
    ]

    for p in processes:
        p.start()

    while not SHUTDOWN:
        for p in processes:
            p.poll_and_restart()
        time.sleep(0.5)

    log_event("Shutting down supervised processes...")
    for p in processes:
        p.terminate()
    log_event("Supervisor stopped cleanly.")


if __name__ == "__main__":
    main()
