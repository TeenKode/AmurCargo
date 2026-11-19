"""Check that OFFLINE.html contains the current, complete user-facing pages."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
bundle = (ROOT / "OFFLINE.html").read_text(encoding="utf-8")
match = re.search(r'<script id="bundleData" type="application/json">([\s\S]*?)</script>', bundle)
assert match, "Embedded page data not found"
pages = json.loads(match.group(1))
expected = {
    "sim": "simulator/Open_Simulation_3D.html",
    "assembly": "simulator/Assembly_Guide_RU.html",
    "purchase": "simulator/Purchase_List_RU.html",
    "quick": "tools/quick_guide_body.html",
    "calibration": "tools/calibration_guide_body.html",
}
assert set(pages) == set(expected), f"Missing/unexpected sections: {set(pages) ^ set(expected)}"
for name, file in expected.items():
    source = (ROOT / file).read_text(encoding="utf-8")
    page = pages[name]["html"]
    if name in ("quick", "calibration"):
        assert source in page, f"Outdated guide: {name}"
    else:
        assert source == page, f"Outdated HTML page: {name}"
    assert "<!doctype html>" in page.lower()
    assert not re.search(r'<script\b[^>]*\bsrc\s*=', page, re.I)
    assert not re.search(r'<link\b[^>]*\bhref\s*=', page, re.I)
    print("OK", name, len(page), "characters")
assert 'srcdoc=pages[id].html' in bundle
assert 'frame.setAttribute(\'allow\',\'serial; usb\')' in bundle
print("PASS: OFFLINE.html includes all current pages and no external runtime assets")
