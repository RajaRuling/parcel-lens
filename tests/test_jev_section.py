"""The Jev section's numbers must match the saved measurements (offline, deterministic)."""
import json
from html.parser import HTMLParser
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
ORIGINAL = Path(__file__).resolve().parents[2] / "jev-vision" / "results" / "parcels.json"


class Grab(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.found, self.in_jev, self.text = [], {}, False, ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section" and a.get("id") == "jev":
            self.in_jev = True
        if self.in_jev:
            self.text += " "
        if self.in_jev and "data-jev" in a:
            self.stack.append((a["data-jev"], tag, ""))
        elif self.stack:
            self.stack.append((None, tag, ""))

    def handle_endtag(self, tag):
        if self.stack:
            key, t, _ = self.stack.pop()
            if key:
                self.found[key] = " ".join(self.found.get(key + "__buf", "").split())
        if tag == "section" and self.in_jev:
            self.in_jev = False

    def handle_data(self, data):
        if self.in_jev:
            self.text += data
        for i in range(len(self.stack)):
            k = self.stack[i][0]
            if k:
                self.found[k + "__buf"] = self.found.get(k + "__buf", "") + data


def shown():
    g = Grab()
    g.feed((DOCS / "index.html").read_text())
    return {k: v for k, v in g.found.items() if not k.endswith("__buf")}, " ".join(g.text.split())


def test_numbers_match_results():
    r = json.loads((DOCS / "jev" / "parcels.json").read_text())
    s, _ = shown()
    pct = lambda x: f"{round(x * 100)}%"
    assert s["n"] == str(r["n"])
    assert s["auc_100"] == str(round(r["auc"][0] * 100))
    assert s["local_auc_100"] == str(round(r["local_auc"][0] * 100))
    assert s["recall_pct"] == str(round(r["recall"][0] * 100))
    assert s["false_alarms"] == str(int(r["clean_false_alarms_per_1000"][0]))
    assert s["box_share_pct"] == pct(r["iou_share_ge_0.5"][0])
    assert s["iou_median_pct"] == pct(r["iou_median"][0])
    assert s["centre_pct"] == pct(r["iou_median_centre_guess"])
    assert s["clean_boxes"] == str(r["clean_boxes_returned"])
    assert s["clean_n"] == str(r["clean_n"])
    assert s["speed"] == f"{r['latency']['p50']:.2f} s"
    assert s["tokens"] == f"about {round(r['tokens']['mean_input'])} input"


def test_recall_is_about_one_in_six():
    r = json.loads((DOCS / "jev" / "parcels.json").read_text())
    assert 1 / 7 < r["recall"][0] < 1 / 5


def test_labels_and_limits_present():
    _, text = shown()
    for needle in ["EXPERIMENTAL", "jev-1.14.0", "one fixed prompt", "nothing tuned", "never 59% with 7%",
                   "presence check must come first", "promising for locating damage",
                   "not yet a replacement for a model trained on your own pictures", "enlarged 2x",
                   "same answer if asked again"]:
        assert needle in text, needle
    assert "demo" not in text.lower().replace("demonstration", "")


def test_example_images_exist_and_are_small():
    names = sorted(p.name for p in (DOCS / "jev").glob("*.png"))
    assert len(names) == 4
    assert all((DOCS / "jev" / n).stat().st_size < 100_000 for n in names)
    html = (DOCS / "index.html").read_text()
    assert all(f"jev/{n}" in html for n in names)


def test_copy_equals_original_when_present():
    if ORIGINAL.exists():
        assert ORIGINAL.read_text() == (DOCS / "jev" / "parcels.json").read_text()
