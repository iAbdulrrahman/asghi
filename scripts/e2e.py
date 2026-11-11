"""Standalone runner for Asghi live end-to-end integration test."""
import sys
import subprocess

def main():
    print("=== Running Asghi Live End-to-End Integration Suite ===")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/test_live_e2e_integration.py", "-v"])
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
