"""Validation test for Android Network Security Config.
Ensures local loopback addresses (10.0.2.2, 127.0.0.1, localhost) allow cleartext HTTP
while maintaining strict HTTPS for arbitrary endpoints in release builds.
"""
import os
import xml.etree.ElementTree as ET
import pytest

MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "mobile", "android", "app", "src", "main", "AndroidManifest.xml"
)
CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "mobile", "android", "app", "src", "main", "res", "xml", "network_security_config.xml"
)


def test_network_security_config_exists_and_linked_in_manifest():
    # 1. Manifest check
    assert os.path.exists(MANIFEST_PATH), f"Manifest not found: {MANIFEST_PATH}"
    manifest_tree = ET.parse(MANIFEST_PATH)
    manifest_root = manifest_tree.getroot()

    app_node = manifest_root.find("application")
    assert app_node is not None, "Application tag not found in AndroidManifest.xml"

    # Android namespace
    android_ns = "{http://schemas.android.com/apk/res/android}"
    security_config_attr = app_node.attrib.get(f"{android_ns}networkSecurityConfig")
    assert security_config_attr == "@xml/network_security_config", (
        f"Expected networkSecurityConfig='@xml/network_security_config', got '{security_config_attr}'"
    )

    # 2. Config XML check
    assert os.path.exists(CONFIG_PATH), f"network_security_config.xml not found at {CONFIG_PATH}"
    config_tree = ET.parse(CONFIG_PATH)
    config_root = config_tree.getroot()
    assert config_root.tag == "network-security-config"

    # 3. Base config must disallow cleartext by default
    base_config = config_root.find("base-config")
    assert base_config is not None, "base-config missing from network_security_config.xml"
    assert base_config.attrib.get("cleartextTrafficPermitted") == "false", (
        "base-config must have cleartextTrafficPermitted='false'"
    )

    # 4. Domain config must allow cleartext ONLY for loopback / local dev
    domain_configs = config_root.findall("domain-config")
    assert len(domain_configs) >= 1, "At least one domain-config required"

    allowed_domains = set()
    for dc in domain_configs:
        if dc.attrib.get("cleartextTrafficPermitted") == "true":
            for d in dc.findall("domain"):
                allowed_domains.add(d.text.strip())

    expected_loopbacks = {"10.0.2.2", "127.0.0.1", "localhost"}
    assert expected_loopbacks.issubset(allowed_domains), (
        f"Missing expected loopbacks in permitted domains: {expected_loopbacks - allowed_domains}"
    )

    # Ensure no arbitrary/wildcard domains permitted
    for d in allowed_domains:
        assert d in expected_loopbacks, f"Unexpected cleartext domain permitted: {d}"
