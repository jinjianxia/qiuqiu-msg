import os
import re
import requests
import json

XUEQIU_USER_ID = os.getenv("XUEQIU_USER_ID")
DING_WEBHOOK = os.getenv("DING_WEBHOOK")
SENT_FILE = "/tmp/sent_posts.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://xueqiu.com/",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}

def load_sent():
    try:
        return set(open(SENT_FILE, "r", encoding="utf-8").read().splitlines())
    except:
        return set()

def save_sent(sid):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        f.write(sid + "\n")

def send_ding(content, link):
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "qiuqiu更新",
            "text": f"**🔔 qiuqiu新动态**\n\n{content}\n\n[原文]({link})"
        }
    }
    requests.post(DING_WEBHOOK, json=msg)

def main():
    url = f"https://xueqiu.com/u/{XUEQIU_USER_ID}"
    print("访问主页：", url)
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("主页请求失败：", e)
        return

    # 抓内嵌JSON
    m = re.search(r'window\.SNB\.pageInitialData\s*=\s*({.*?});', r.text, re.S)
    if not m:
        print("未找到数据")
        return

    try:
        data = json.loads(m.group(1))
        statuses = data.get("statuses", [])
        print("抓到动态数：", len(statuses))
    except:
        print("JSON解析失败")
        return

    sent = load_sent()
    for s in statuses:
        sid = str(s["id"])
        if sid in sent:
            continue
        content = s["text"]
        link = f"https://xueqiu.com/statuses/{sid}.html"
        send_ding(content, link)
        save_sent(sid)
        print("已发送：", sid)

if __name__ == "__main__":
    main()
