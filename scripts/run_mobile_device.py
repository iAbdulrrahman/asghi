"""Automated runner for live Flutter integration tests and screenshot capture on Android device/emulator."""
import os
import sys
import time
import socket
import urllib.request
import subprocess
import shutil

sys.path.insert(0, os.path.abspath("."))

ADB_BIN = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
FLUTTER_BIN = r"C:\flutter\bin\flutter.bat"
if not os.path.exists(FLUTTER_BIN):
    FLUTTER_BIN = shutil.which("flutter") or "flutter"

PORT = 8000
DB_PATH = "test_device_e2e.db"


def wait_for_server(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def get_first_device() -> str:
    res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True, check=True)
    lines = res.stdout.strip().splitlines()[1:]
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0]
    return ""


def main():
    print("=== Asghi Live Android Integration Test Runner ===")
    device_id = get_first_device()
    if not device_id:
        print("ERROR: No authorized Android device/emulator found via adb.")
        sys.exit(1)
    print(f"Target device: {device_id}")

    # Seed fresh test database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    from asghi.seed import seed_database
    seed_database(DB_PATH)
    print(f"Seeded database at {DB_PATH}")

    # Reverse port 8000 so device can reach host 127.0.0.1:8000
    subprocess.run([ADB_BIN, "-s", device_id, "reverse", f"tcp:{PORT}", f"tcp:{PORT}"], check=True)
    print(f"Configured adb reverse tcp:{PORT} -> tcp:{PORT}")

    # Start FastAPI server
    env = os.environ.copy()
    env["ASGHI_DB_PATH"] = DB_PATH
    env["PYTHONUNBUFFERED"] = "1"
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "asghi.api:app", "--host", "127.0.0.1", "--port", str(PORT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"Started FastAPI backend server on pid {server_proc.pid}")

    try:
        health_url = f"http://127.0.0.1:{PORT}/healthz"
        if not wait_for_server(health_url):
            print("ERROR: Backend server failed to start within timeout.")
            sys.exit(1)
        print("Backend server healthy!")

        # Run Flutter integration test
        print("Running Flutter integration test on device...")
        mobile_dir = os.path.abspath("mobile")
        test_cmd = [
            FLUTTER_BIN,
            "test",
            "integration_test/app_test.dart",
            "-d",
            device_id,
            f"--dart-define=API_BASE=http://127.0.0.1:{PORT}",
        ]
        test_res = subprocess.run(test_cmd, cwd=mobile_dir)
        print(f"Integration test exited with code: {test_res.returncode}")

        # Capture device screenshot
        screenshot_path = os.path.join(mobile_dir, "docs", "device_flow_1.png")
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        with open(screenshot_path, "wb") as f:
            subprocess.run([ADB_BIN, "-s", device_id, "exec-out", "screencap", "-p"], stdout=f, check=True)
        print(f"Captured device screenshot saved to {screenshot_path}")

        if test_res.returncode != 0:
            sys.exit(test_res.returncode)

    finally:
        print("Stopping backend server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        print("Cleaned up server and test database.")


if __name__ == "__main__":
    main()
