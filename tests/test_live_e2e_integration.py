"""Live E2E integration test against a running FastAPI backend.
Spawns a clean server process, seeds database, and executes all 5 domain flows.
"""
import os
import sys
import time
import socket
import subprocess
import tempfile
import pytest

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class LiveServerContext:
    def __init__(self, db_path: str, port: int):
        self.db_path = db_path
        self.port = port
        self.process = None

    def start(self):
        env = os.environ.copy()
        env["ASGHI_DATABASE_URL"] = f"sqlite:///{self.db_path}"
        env["PYTHONUNBUFFERED"] = "1"
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "asghi.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--log-level",
            "warning",
        ]
        self.process = subprocess.Popen(cmd, env=env)

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            self.process = None
