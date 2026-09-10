"""公開サイトへ反映する。

    python3 deploy.py            # 反映
    python3 deploy.py "メモ"     # コミットメッセージを指定

やること:
  1. 版番号(APP_BUILD)を今の日時で振り直し、data/version.json も同じ値にする
  2. コミットして push
  3. GitHub Pages に届くまで待って、中身を確かめる

版番号を1か所で更新するので、「上げたのに反映されない」を仕組みで防ぐ。
"""
import datetime, json, os, re, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://taku10-web.github.io/uchinotana/"
GH = os.path.expanduser("~/.local/bin/gh")


def run(*args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)


def main():
    os.chdir(ROOT)
    build = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")

    # 版番号を index.html と version.json でそろえる
    path = os.path.join(ROOT, "index.html")
    html = open(path, encoding="utf-8").read()
    html, n = re.subn(r'const APP_BUILD = "[^"]*";', f'const APP_BUILD = "{build}";', html)
    if n != 1:
        print("!! APP_BUILD が見つかりません（index.html を確認してください）")
        return 1
    open(path, "w", encoding="utf-8").write(html)
    json.dump({"build": build}, open(os.path.join(ROOT, "data/version.json"), "w",
              encoding="utf-8"), ensure_ascii=False)
    print(f"版番号: {build}")

    msg = sys.argv[1] if len(sys.argv) > 1 else f"更新 {build}"
    run("git", "add", "-A")
    if not run("git", "diff", "--cached", "--quiet").returncode:
        print("変更がありません。")
        return 0
    r = run("git", "commit", "-m", msg)
    if r.returncode:
        print("!! コミット失敗\n" + r.stderr)
        return 1
    r = run("git", "push", "origin", "main")
    if r.returncode:
        print("!! push 失敗\n" + r.stderr)
        print("   ログインが切れている場合: ~/.local/bin/gh auth login")
        return 1
    print("push 完了。GitHub Pages の反映を待ちます…")

    for i in range(24):
        time.sleep(10)
        try:
            url = SITE + f"data/version.json?t={int(time.time())}"
            req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
            live = json.load(urllib.request.urlopen(req, timeout=15))
            if live.get("build") == build:
                print(f"反映されました（{(i + 1) * 10}秒）")
                print(f"  {SITE}")
                return 0
        except Exception:
            pass
        print(f"  待機中… {(i + 1) * 10}秒")
    print("!! 4分待っても反映されませんでした。GitHubのActionsタブを確認してください。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
