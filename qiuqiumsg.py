import os
import re
import requests
import json

# ===================== 【敏感配置 - 从环境变量读取】 =====================
XUEQIU_USER_ID = os.getenv("XUEQIU_USER_ID")
DING_WEBHOOK = os.getenv("DING_WEBHOOK")

# 去重记录
SENT_FILE = "/tmp/sent_posts.txt"

# 请求头保持原版（不改！保证能正常抓取）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://xueqiu.com/",
}

# ===================== 去重功能 =====================
def load_sent_ids():
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    except:
        return set()

def save_sent_id(sid):
    try:
        with open(SENT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{sid}\n")
    except:
        pass

# ===================== 发送到钉钉 =====================
def send_to_ding(content, link):
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "雪球动态更新",  # 这里隐藏
            "text": f"**🔔 雪球博主新动态**\n\n{content}\n\n[查看原文]({link})"
        }
    }
    try:
        requests.post(DING_WEBHOOK, json=message, timeout=10)
    except:
        pass

# ===================== 核心抓取（代码完全不变） =====================
def fetch_posts():
    url = f"https://xueqiu.com/u/{XUEQIU_USER_ID}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except:
        print("请求失败")
        return

    match = re.search(r'"statuses":(\[.*?\]),"user"', resp.text, re.S)
    if not match:
        print("未获取到内容")
        return

    try:
        status_list = json.loads(match.group(1))
    except:
        print("解析失败")
        return

    sent = load_sent_ids()

    for status in status_list:
        sid = str(status.get("id", ""))
        if not sid or sid in sent:
            continue

        content = status.get("text", "无内容")
        link = f"https://xueqiu.com/statuses/{sid}.html"

        send_to_ding(content, link)
        save_sent_id(sid)
        print(f"已发送新动态：{sid}")

# ===================== 启动 =====================
if __name__ == "__main__":
    fetch_posts()
