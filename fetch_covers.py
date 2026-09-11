#!/usr/bin/env python3
"""ボドゲーマの表紙画像を data/covers/<slug>.jpg に保存する（棚の画像書き出し用）。
CDNにCORSヘッダーが無く canvas で描けないため、同一オリジンにコピーを置く。"""
import json, os, re, sys, time, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__))
games = json.load(open(os.path.join(ROOT, "data/games.json")))
out = os.path.join(ROOT, "data/covers"); os.makedirs(out, exist_ok=True)
SIZE = "dw=auto,dh=300,cw=400,ch=300,da=l,ds=s,q=85,cc=FFFFFF"
done = skipped = failed = 0
for g in games:
    slug = g["url"].rstrip("/").split("/")[-1]
    dst = os.path.join(out, slug + ".jpg")
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        skipped += 1; continue
    src = re.sub(r"small_light\([^)]*\)", "small_light(" + SIZE + ")", g["img"])
    try:
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=20).read()
        if data.startswith(b"\x89PNG") or data[8:12] == b"WEBP":
            # PNG/WebPはmacOSのsipsでJPEGに変換して保存する
            import subprocess
            tmp = dst + (".tmp.png" if data.startswith(b"\x89PNG") else ".tmp.webp"); open(tmp, "wb").write(data)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", tmp, "--out", dst], check=True, capture_output=True)
            os.remove(tmp)
        elif data.startswith(b"\xff\xd8"):
            open(dst, "wb").write(data)
        else:
            raise ValueError("unknown image type")
        done += 1
        time.sleep(0.15)
    except Exception as e:
        failed += 1; print("NG", slug, e, file=sys.stderr)
print(f"saved {done}, skipped {skipped}, failed {failed}")
