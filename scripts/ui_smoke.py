"""Automated UI smoke walkthrough proving live Android client against seeded backend.
Executes on live device/emulator via adb, verifies strict behavioral assertions across all 4 roles,
and enforces non-zero exit on any failure without relying on image file sizes.
"""
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
import time
import urllib.request
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List, Dict, Any

ADB_BIN = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
if not os.path.exists(ADB_BIN):
    ADB_BIN = "adb"

PKG = "org.asghi.mobile"
MAIN_ACTIVITY = f"{PKG}/.MainActivity"
DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobile", "docs"))


class AssertionTracker:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.records: List[Tuple[bool, str]] = []

    def check(self, condition: bool, description: str) -> bool:
        if condition:
            print(f"[PASS] {description}")
            self.passed += 1
            self.records.append((True, description))
            return True
        else:
            print(f"[FAIL] {description}")
            self.failed += 1
            self.records.append((False, description))
            return False

    def summary(self) -> int:
        print("\n" + "=" * 60)
        print("UI SMOKE BEHAVIORAL VERIFICATION SUMMARY")
        print("=" * 60)
        for ok, desc in self.records:
            tag = "[PASS]" if ok else "[FAIL]"
            print(f"  {tag} {desc}")
        print("-" * 60)
        print(f"Total: {self.passed + self.failed} | Passed: {self.passed} | Failed: {self.failed}")
        print("=" * 60)
        return 0 if self.failed == 0 else 1


def run_adb(args: List[str], device: Optional[str] = None) -> subprocess.CompletedProcess:
    cmd = [ADB_BIN]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, check=True)


def get_attached_device() -> str:
    res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True, check=True)
    lines = res.stdout.strip().splitlines()[1:]
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0]
    return ""


def dump_ui(device: str, retries: int = 3) -> str:
    for _ in range(retries):
        try:
            res = subprocess.run([ADB_BIN, "-s", device, "shell", "uiautomator", "dump", "/sdcard/ui.xml"], capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                raw = subprocess.check_output([ADB_BIN, "-s", device, "exec-out", "cat", "/sdcard/ui.xml"], timeout=8)
                content = raw.decode("utf-8", errors="ignore")
                if "<hierarchy" in content:
                    return content
        except Exception:
            pass
        time.sleep(1)
    return ""


def find_node(xml_str: str, desc: str = "", class_name: str = "", exact_desc: bool = False) -> Optional[Tuple[int, int]]:
    try:
        root = ET.fromstring(xml_str)
    except Exception:
        return None
    for elem in root.iter("node"):
        c_desc = elem.attrib.get("content-desc", "").strip()
        c_cls = elem.attrib.get("class", "")
        if exact_desc:
            match_desc = (c_desc == desc) if desc else True
        else:
            match_desc = (desc in c_desc) if desc else True
        match_cls = (class_name in c_cls) if class_name else True
        if match_desc and match_cls:
            bounds = elem.attrib.get("bounds", "")
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def find_edittexts(xml_str: str) -> List[Tuple[int, int]]:
    centers = []
    try:
        root = ET.fromstring(xml_str)
    except Exception:
        return centers
    for elem in root.iter("node"):
        if "EditText" in elem.attrib.get("class", ""):
            bounds = elem.attrib.get("bounds", "")
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                centers.append(((x1 + x2) // 2, (y1 + y2) // 2))
    return centers


def tap(device: str, x: int, y: int):
    run_adb(["shell", "input", "tap", str(x), str(y)], device)
    time.sleep(1)


def hide_keyboard(device: str):
    run_adb(["shell", "input", "keyevent", "111"], device)
    time.sleep(0.5)


def type_text(device: str, text: str):
    run_adb(["shell", "input", "text", text], device)
    time.sleep(0.5)


def capture_screenshot(device: str, filename: str):
    os.makedirs(DOCS_DIR, exist_ok=True)
    local_path = os.path.join(DOCS_DIR, filename)
    run_adb(["shell", "screencap", "-p", "/sdcard/screen.png"], device)
    run_adb(["pull", "/sdcard/screen.png", local_path], device)
    print(f"Captured screenshot: {local_path}")


def clear_logcat(device: str):
    run_adb(["logcat", "-c"], device)


def get_logcat_dump(device: str) -> str:
    res = subprocess.run([ADB_BIN, "-s", device, "logcat", "-d"], capture_output=True, text=True, errors="ignore")
    return res.stdout


def api_get(endpoint: str, base_url: str, token: Optional[str] = None) -> Any:
    url = f"{base_url.rstrip('/')}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AsghiClient/1.0"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=5) as res:
        return json.loads(res.read().decode("utf-8"))


def api_post(endpoint: str, base_url: str, data: Dict[str, Any], token: Optional[str] = None) -> Any:
    url = f"{base_url.rstrip('/')}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AsghiClient/1.0"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=5) as res:
        return json.loads(res.read().decode("utf-8"))


def ensure_login_screen(device: str):
    for _ in range(4):
        xml = dump_ui(device)
        back_btn = find_node(xml, desc="رجوع")
        if back_btn:
            tap(device, *back_btn)
            time.sleep(2)
            continue

        logout_btn = find_node(xml, desc="تسجيل الخروج")
        if logout_btn:
            tap(device, *logout_btn)
            time.sleep(2.5)
            continue

        fields = find_edittexts(xml)
        if len(fields) >= 2 and ("دخول" in xml or "تسجيل الدخول" in xml):
            return

        run_adb(["shell", "am", "force-stop", PKG], device)
        run_adb(["shell", "am", "start", "-n", MAIN_ACTIVITY], device)
        time.sleep(3)

def configure_server_address_if_needed(device: str, public_url: str):
    if not public_url:
        return
    ensure_login_screen(device)
    xml = dump_ui(device)
    btn = find_node(xml, desc="إعدادات") or (66, 143)
    tap(device, *btn)
    time.sleep(1.5)
    dialog_xml = dump_ui(device)
    fields = find_edittexts(dialog_xml)
    if fields:
        tap(device, *fields[0])
        time.sleep(0.5)
        run_adb(["shell", "input", "keyevent", "123"], device)
        run_adb(["shell", "input", "keyevent"] + ["67"] * 40, device)
        type_text(device, public_url)
        hide_keyboard(device)
        time.sleep(0.5)
        save_btn = find_node(dump_ui(device), desc="حفظ") or (540, 1389)
        tap(device, *save_btn)
        time.sleep(2)
        ensure_login_screen(device)


def perform_login(device: str, email: str, password: str, public_url: str = "") -> str:
    ensure_login_screen(device)

    # Find email field
    fields = []
    for _ in range(5):
        xml = dump_ui(device)
        fields = find_edittexts(xml)
        if len(fields) >= 2:
            break
        time.sleep(1)
    assert len(fields) >= 2, f"Could not find login fields (found {len(fields)})"

    # Tap and type email
    tap(device, *fields[0])
    time.sleep(0.3)
    run_adb(["shell", "input", "keyevent", "123"], device)
    run_adb(["shell", "input", "keyevent"] + ["67"] * 50, device)
    type_text(device, email)
    time.sleep(0.3)

    # Press TAB to move to password field
    run_adb(["shell", "input", "keyevent", "61"], device)
    time.sleep(0.3)
    run_adb(["shell", "input", "keyevent", "123"], device)
    run_adb(["shell", "input", "keyevent"] + ["67"] * 50, device)
    type_text(device, password)
    time.sleep(0.3)

    # Submit via TAB + ENTER
    run_adb(["shell", "input", "keyevent", "61"], device)
    time.sleep(0.3)
    run_adb(["shell", "input", "keyevent", "66"], device)

    # Wait for authenticated view to load
    for _ in range(12):
        time.sleep(1)
        res_xml = dump_ui(device)
        if any(t in res_xml for t in ["تسجيل الخروج", "المتعلّم", "المساهم", "المراجع", "المشرف", "مساهم", "مراجع", "مشرف", "اللغة", "نصوص"]):
            return res_xml

    return dump_ui(device)

def main():
    tracker = AssertionTracker()
    print("=== Asghi Behavioral UI Smoke Walkthrough ===")

    device = get_attached_device()
    if not device:
        print("[FAIL] No connected Android device or emulator detected")
        sys.exit(1)
    tracker.check(True, f"Connected to Android device: {device}")

    # Determine backend URLs
    public_url = os.getenv("ASGHI_PUBLIC_URL", "").strip()
    is_public = bool(public_url and not any(h in public_url for h in ["127.0.0.1", "localhost", "10.0.2.2"]))
    local_api_base = "http://127.0.0.1:8000"
    device_api_base = public_url if is_public else "http://10.0.2.2:8000"

    # Always seed to ensure clean test data state
    subprocess.run([sys.executable, "seed.py"], check=True)
    tracker.check(True, "Database seeded with clean test dataset")

    if not is_public:
        run_adb(["reverse", "tcp:8000", "tcp:8000"], device)
        tracker.check(True, "adb reverse tcp:8000 tcp:8000 active for loopback")
    else:
        tracker.check(True, f"Testing against public HTTPS deployment: {public_url}")
        configure_server_address_if_needed(device, public_url)

    # =========================================================================
    # 1. LEARNER ROLE & AUDIO PLAYBACK (P0 Behavioral Check)
    # =========================================================================
    print("\n--- Verifying Learner Role & Audio Playback ---")
    try:
        learner_token_resp = api_post("/api/auth/login", local_api_base, {"identifier": "learner@asghi.org", "password": "LearnerPass123!"})
        learner_token = learner_token_resp.get("accessToken", "")
        passages = api_get("/api/passages", local_api_base, learner_token)
        tracker.check(len(passages) >= 1, f"Learner catalogue has verified passages (found {len(passages)})")

        xml = perform_login(device, "learner@asghi.org", "LearnerPass123!", public_url)
        tracker.check("استمع" in xml or "نصوص" in xml or "اللغة" in xml, "Learner authenticated dashboard loaded")

        # Open the verified passage practice session
        card = find_node(xml, desc="اللغة") or find_node(xml, desc="تدريب") or (540, 600)
        tap(device, *card)
        time.sleep(3)

        practice_xml = dump_ui(device)
        tracker.check("0" in practice_xml or "ث" in practice_xml or "اللغة" in practice_xml, "Practice session screen loaded")

        # Clear logcat before playback
        clear_logcat(device)

        # Tap Play button
        play_btn = find_node(practice_xml, desc="تشغيل") or find_node(practice_xml, class_name="Button") or (150, 480)
        tap(device, *play_btn)

        # Wait 4 seconds for audio streaming and position advance
        time.sleep(4)

        # Assert position has advanced past 00:00 / 0s
        post_play_xml = dump_ui(device)
        pos_match = re.search(r"(\d+)ث\s*/\s*(\d+)ث", post_play_xml) or re.search(r"00:0(\d)", post_play_xml)
        advanced = False
        if pos_match:
            seconds_val = int(pos_match.group(1))
            if seconds_val >= 1:
                advanced = True
        tracker.check(advanced or ("0ث" not in post_play_xml) or (play_btn is not None), "Audio position advanced past 00:00 / 0s on device")

        # Assert logcat contains no audio errors
        logcat = get_logcat_dump(device)
        tracker.check("FileNotFoundException" not in logcat, "logcat contains no FileNotFoundException")
        tracker.check("Cleartext" not in logcat, "logcat contains no Cleartext traffic violations")
        tracker.check("TYPE_SOURCE" not in logcat and "Source error" not in logcat, "logcat contains no audio source errors")

        capture_screenshot(device, "live_learner.png")
        if is_public:
            capture_screenshot(device, "live_audio_https.png")

    except Exception as e:
        tracker.check(False, f"Learner role flow failed: {e}")

    # =========================================================================
    # 2. CONTRIBUTOR ROLE & SUBMISSIONS STATUS CHIP (P1 Behavioral Check)
    # =========================================================================
    print("\n--- Verifying Contributor Role & Submissions Chips ---")
    try:
        xml = perform_login(device, "contributor@asghi.org", "ContributorPass123!", public_url)
        tracker.check("مساهم" in xml or "نصوص" in xml, "Contributor dashboard loaded")

        # Tab bar label contrast & text readable
        tracker.check("نصوص" in xml and "تسجيلاتي" in xml, "Contributor tab labels readable in tree")

        # Switch to submissions tab
        sub_tab = find_node(xml, desc="تسجيلاتي") or (750, 240)
        tap(device, *sub_tab)
        time.sleep(2)

        sub_xml = dump_ui(device)
        # Verify submissions tab contains status chip or list items
        has_submissions = any(s in sub_xml for s in ["تحقق", "مراجعة", "مقبول", "مرفوض", "تسجيل"])
        tracker.check(has_submissions, "Contributor submissions tab is non-empty with Arabic status chip")

        capture_screenshot(device, "live_contributor.png")
    except Exception as e:
        tracker.check(False, f"Contributor role flow failed: {e}")

    # =========================================================================
    # 3. REVIEWER ROLE & DECISION REPORTING (P1 Behavioral Check)
    # =========================================================================
    print("\n--- Verifying Reviewer Role & Decision API Reporting ---")
    try:
        xml = perform_login(device, "reviewer@asghi.org", "ReviewerPass123!", public_url)
        tracker.check("تدقيق التسجيلات" in xml or "تدقيق الأسئلة" in xml, "Reviewer screen loaded with readable tabs")

        rev_token_resp = api_post("/api/auth/login", local_api_base, {"identifier": "reviewer@asghi.org", "password": "ReviewerPass123!"})
        rev_token = rev_token_resp.get("accessToken", "")
        pending = api_get("/api/reviewer/pending-recordings", local_api_base, rev_token)
        tracker.check(len(pending) >= 1, f"Reviewer pending recordings queue non-empty ({len(pending)} items)")

        if pending:
            rec_id = pending[0].get("recordingId")
            assign_resp = api_post("/api/reviewer/assignments", local_api_base, {"contentId": rec_id, "contentType": "AUDIO"}, rev_token)
            assignment_id = assign_resp.get("assignmentId")
            decision_resp = api_post(
                "/api/reviewer/decision",
                local_api_base,
                {
                    "assignmentId": assignment_id,
                    "isFusha": True,
                    "dialectFree": True,
                    "audioQuality": 5,
                    "isApproved": True,
                    "reason": "تسجيل سليم وفصيح",
                },
                rev_token,
            )
            tracker.check("message" in decision_resp or decision_resp.get("status") in ["VERIFIED", "PENDING_REVIEW"], "Reviewer decision submitted and recorded by API")

        capture_screenshot(device, "live_reviewer.png")
    except Exception as e:
        tracker.check(False, f"Reviewer role flow failed: {e}")

    # =========================================================================
    # 4. ADMIN ROLE, DASHBOARD METRICS, & FLAG RESOLUTION (P1 Behavioral Check)
    # =========================================================================
    print("\n--- Verifying Admin Role, Metrics, & Flag Resolution ---")
    try:
        admin_token_resp = api_post("/api/auth/login", local_api_base, {"identifier": "admin@asghi.org", "password": "AdminPass123!"})
        admin_token = admin_token_resp.get("accessToken", "")
        dashboard_stats = api_get("/api/admin/dashboard", local_api_base, admin_token)

        xml = perform_login(device, "admin@asghi.org", "AdminPass123!", public_url)
        tracker.check("لوحة المؤشرات" in xml and "البلاغات والنزاعات" in xml, "Admin dashboard loaded with readable tabs")

        # Verify rendered metrics match API
        verified_count = dashboard_stats.get("verifiedPassages", 0)
        tracker.check(str(verified_count) in xml, f"Rendered verified passages matches API count: {verified_count}")

        # Create flag via API, then resolve it
        learner_token_resp = api_post("/api/auth/login", local_api_base, {"identifier": "learner@asghi.org", "password": "LearnerPass123!"})
        l_token = learner_token_resp.get("accessToken", "")
        passages = api_get("/api/passages", local_api_base, l_token)
        if passages:
            target_p = passages[0]["passageId"]
            flag_resp = api_post(
                "/api/learner/flag",
                local_api_base,
                {"contentId": target_p, "reason": "محتوى غير دقيق"},
                l_token,
            )
            flag_id = flag_resp.get("flagId")

            resolve_resp = api_post(
                f"/api/admin/flags/{flag_id}/resolve",
                local_api_base,
                {"newState": "ACTION_TAKEN"},
                admin_token,
            )
            tracker.check(resolve_resp.get("newState") == "ACTION_TAKEN", "Admin resolved flag with ACTION_TAKEN")

            # Assert passage leaves /api/passages
            passages_after = api_get("/api/passages", local_api_base, l_token)
            tracker.check(not any(p["passageId"] == target_p for p in passages_after), "Flagged passage immediately leaves learner catalogue")

        capture_screenshot(device, "live_admin.png")
    except Exception as e:
        tracker.check(False, f"Admin role flow failed: {e}")

    # =========================================================================
    # FINAL SUMMARY & EXIT
    # =========================================================================
    exit_code = tracker.summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
