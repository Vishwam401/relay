# Day 2: Signals & Process Death Experiment (SIGTERM vs SIGKILL)


import os
import signal
import sys
import time

shutdown_requested = False

def handle_signal(signum, frame):
    global shutdown_requested
    print(f"\n[SIGNAL] Signal {signum} received! Initiating shutdown...")
    shutdown_requested = True

def run_worker_finish_current(total_steps=5):
    # Signal handlers registered
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    print(f"[WORKER] PID: {os.getpid()} starting...")
    job_id = 1
    
    while not shutdown_requested:
        print(f"\n[JOB {job_id}] Started ({total_steps}s task)...")
        for step in range(total_steps):
            time.sleep(1)
            print(f"[JOB {job_id}] Step {step + 1}/{total_steps}...")
            
        print(f"[JOB {job_id}] Completed successfully!")
        job_id += 1
        
        if shutdown_requested:
            print("[SHUTDOWN] Signal flag is True. Not taking next job.")
            
    print("[CLEANUP] Flush logs, release DB connections, exit cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    run_worker_finish_current(total_steps=30)







