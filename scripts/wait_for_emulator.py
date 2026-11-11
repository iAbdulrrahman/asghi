import subprocess
import time
import os

adb = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")

print(f"Waiting for device via {adb}...")
subprocess.run([adb, "wait-for-device"], check=True)
print("Device attached. Polling sys.boot_completed...")

for i in range(120):
    res = subprocess.run([adb, "shell", "getprop", "sys.boot_completed"], capture_output=True, text=True)
    val = res.stdout.strip()
    if val == "1":
        print(f"Emulator booted successfully! (iteration {i+1})")
        break
    time.sleep(2)
else:
    print("Timed out waiting for boot completion.")
    exit(1)
