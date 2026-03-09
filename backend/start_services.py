"""
start_services.py — Launch all microservices in one command.

Usage:
    cd backend
    source venv/bin/activate
    python start_services.py

This spawns each FastAPI service on its own port.  Press Ctrl+C to
stop all services at once.
"""

import subprocess
import sys
import signal
import os

SERVICES = [
    ("parking_service.main:app",     8001, "Parking"),
    ("sensor_service.main:app",      8002, "Sensor"),
    ("reservation_service.main:app", 8003, "Reservation"),
    ("pricing_service.main:app",     8004, "Pricing"),
    ("gateway.main:app",             8000, "Gateway"),
]


def main():
    procs: list[subprocess.Popen] = []
    python = sys.executable

    print("Starting Smart Parking System microservices...\n")

    for module, port, name in SERVICES:
        cmd = [
            python, "-m", "uvicorn", module,
            "--port", str(port),
            "--reload",
        ]
        print(f"  [{name:12s}]  port {port}")
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        procs.append(proc)

    print("\nAll services started. Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\nShutting down all services...")
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()
        print("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait for any process to exit
    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
