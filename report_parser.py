"""Extract text from uploaded lab reports (PDF / image) and parse test values."""
import re
from medical_kb import LAB_MARKERS


def extract_text(uploaded_file) -> str:
    """Return raw text from a PDF or image upload. Never raises."""
    name = (uploaded_file.name or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(uploaded_file)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        else:
            from PIL import Image
            import pytesseract
            img = Image.open(uploaded_file)
            return pytesseract.image_to_string(img)
    except Exception as e:  # noqa: BLE001
        return f""


def _clean_number(s: str):
    s = s.replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_markers(text: str):
    """Find known lab markers in free text. Returns list of dicts."""
    t = " " + text.lower().replace("\n", " ") + " "
    t = re.sub(r"\s+", " ", t)
    found = []
    seen = set()
    consumed = []  # spans (start, end) already claimed by a longer alias
    # longest aliases first so "total cholesterol" beats "cholesterol" etc.
    entries = []
    for marker, info in LAB_MARKERS.items():
        for alias in info["aliases"]:
            entries.append((len(alias), marker, alias.strip()))
    entries.sort(reverse=True)

    for _, marker, alias in entries:
        if marker in seen:
            continue
        # alias must not be part of a larger word (e.g. "ast" in "fasting");
        # allow "Count/Level", colons, dashes, parens between alias and value
        sep = r"[\s:\-()]{0,12}(?:count|level|value)?[\s:\-()]{0,12}"
        pat = (r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z])"
               + sep + r"(\d[\d,\.]*)")
        for m in re.finditer(pat, t):
            if not m.group(1):
                continue
            alias_start = m.start()
            if any(s <= alias_start < e for s, e in consumed):
                continue  # inside text already claimed by a longer alias
            val = _clean_number(m.group(1))
            if val is None or val > 10_000_000:
                continue
            break
        else:
            continue
        seen.add(marker)
        consumed.append((alias_start, m.end(1)))
        info = LAB_MARKERS[marker]
        lo, hi = info["range"]
        status = "normal" if lo <= val <= hi else ("low" if val < lo else "high")
        found.append({
            "marker": marker,
            "value": val,
            "unit": info["unit"],
            "range": f"{lo} – {hi} {info['unit']}",
            "status": status,
            "explanation": info["low"] if status == "low" else (info["high"] if status == "high" else "Within the normal reference range. 👍"),
            "tip": info["tip"],
        })
    return found


def parse_pasted(text: str):
    """Parse user-pasted values, one per line like 'Hemoglobin 13.2'."""
    return parse_markers(text)


def summarize(results):
    total = len(results)
    abnormal = [r for r in results if r["status"] != "normal"]
    if total == 0:
        return ("I couldn't detect standard test values in this report. Try a clearer photo/PDF, "
                "or paste values like:\n\nHemoglobin 13.2\nWBC 7500\nPlatelets 220000")
    lines = [f"✅ Analyzed **{total}** markers: **{len(abnormal)}** outside the normal range."]
    if abnormal:
        lines.append("\n**⚠️ Needs attention:**")
        for r in abnormal:
            arrow = "🔻 LOW" if r["status"] == "low" else "🔺 HIGH"
            lines.append(f"- {arrow} **{r['marker']}**: {r['value']} {r['unit']} (normal {r['range']})")
    else:
        lines.append("\n🎉 All detected values are within normal ranges!")
    return "\n".join(lines)
