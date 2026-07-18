"""从浏览器导出的 Cookie 文件加载到 Playwright。

用法:
    1. Chrome 打开 x.com，F12 → Application → Cookies → x.com
    2. 复制每个 Cookie 的 Name 和 Value，写入 twitter/cookies.txt:
       格式: name=value（一行一个）
    3. python -m twitter.import_cookies
"""
import json
from pathlib import Path

COOKIE_FILE = Path(__file__).parent / "cookies.json"
TXT_FILE = Path(__file__).parent / "cookies.txt"


def main():
    if not TXT_FILE.exists():
        print("请创建 twitter/cookies.txt，格式: name=value（一行一个）")
        print("最少需要: auth_token, ct0")
        return False

    cookies = []
    with open(TXT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                name, _, value = line.partition("=")
                cookies.append({"name": name.strip(), "value": value.strip()})

    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    names = {c["name"] for c in cookies}
    print(f"已导入 {len(cookies)} 个 Cookie: {names}")
    if "auth_token" not in names:
        print("警告: 缺少 auth_token（登录关键 Cookie）")
    return True


if __name__ == "__main__":
    main()
