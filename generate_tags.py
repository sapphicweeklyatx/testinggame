"""
Generate name-tag codes, QR images, a private key sheet, and a printable label sheet.

Usage:
    pip install "qrcode[pil]"
    python tools/generate_tags.py --base-url https://sapphichalloween.github.io/ --per-sign 20

Re-running keeps existing codes (stored in tags.json) and only rebuilds the QR images,
so you can change the base URL later without reprinting different codes.
"""
import argparse, csv, json, os, secrets
import qrcode

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
GLYPHS = "♈♉♊♋♌♍♎♏♐♑♒♓"
ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"  # no 0/o/1/l/i look-alikes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def new_code(taken):
    while True:
        c = "".join(secrets.choice(ALPHABET) for _ in range(6))
        if c not in taken:
            taken.add(c)
            return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://sapphichalloween.github.io/")
    ap.add_argument("--per-sign", type=int, default=20)
    args = ap.parse_args()
    if args.per_sign > 22:
        raise SystemExit("Max 22 tags per sign (content pools hold 23 lines).")

    json_path = os.path.join(ROOT, "tags.json")
    tags = json.load(open(json_path)) if os.path.exists(json_path) else {}
    taken = set(tags)
    for s in range(12):
        have = {v[1] for v in tags.values() if v[0] == s}
        for n in range(1, args.per_sign + 1):
            if n not in have:
                tags[new_code(taken)] = [s, n]

    json.dump(tags, open(json_path, "w"), indent=0)
    with open(os.path.join(ROOT, "tags.js"), "w") as f:
        f.write("window.TAGS=" + json.dumps(tags, separators=(",", ":")) + ";\n")

    out = os.path.join(ROOT, "print")
    os.makedirs(os.path.join(out, "qr"), exist_ok=True)
    rows = sorted(tags.items(), key=lambda kv: (kv[1][0], kv[1][1]))
    base = args.base_url if args.base_url.endswith("/") else args.base_url + "/"

    with open(os.path.join(out, "key.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sign", "number", "code", "url"])
        for code, (s, n) in rows:
            url = f"{base}?c={code}"
            w.writerow([SIGNS[s], n, code, url])
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            qr.make_image(fill_color="black", back_color="white").save(os.path.join(out, "qr", f"{code}.png"))

    labels = "".join(
        f'<div class="tag"><div class="sign"><span class="g">{GLYPHS[s]}&#xFE0E;</span>{SIGNS[s]}</div>'
        f'<img src="qr/{code}.png" alt=""><div class="n">#{n}</div></div>'
        for code, (s, n) in rows)
    html = f"""<!doctype html><meta charset="utf-8"><title>Name tags</title>
<style>
@page {{ size: letter; margin: 0.5in; }}
body {{ font-family: Georgia, serif; margin: 0; }}
.sheet {{ display: grid; grid-template-columns: repeat(2, 3.375in); gap: 0.25in 0.5in; }}
.tag {{ height: 2.33in; border: 1px dashed #aaa; display: grid; grid-template-columns: 1fr 1.4in;
        align-items: center; padding: 0 0.2in; position: relative; break-inside: avoid; }}
.sign {{ font-size: 22pt; line-height: 1.1; }}
.g {{ display: block; font-size: 34pt; }}
img {{ width: 1.4in; height: 1.4in; }}
.n {{ position: absolute; bottom: 4px; right: 8px; font-size: 7pt; color: #888; }}
</style>
<p style="font-family:sans-serif">Sized for 2.33" × 3.375" badge labels (e.g. Avery 5395). Adjust .tag size to match your labels. Print test page first.</p>
<div class="sheet">{labels}</div>"""
    open(os.path.join(out, "labels.html"), "w").write(html)
    print(f"{len(tags)} tags → tags.js, print/key.csv, print/qr/, print/labels.html  (base {base})")


if __name__ == "__main__":
    main()
