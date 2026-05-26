import os
import re
import requests
import json

# ========== 配置（保持不变） ==========
XUEQIU_USER_ID = os.getenv("XUEQIU_USER_ID")
DING_WEBHOOK = os.getenv("DING_WEBHOOK")
SENT_FILE = "/tmp/sent_posts.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://xueqiu.com/",
    "Accept": "application/json, text/plain, */*",
}

# ========== 去重 ==========
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

# ========== 发钉钉 ==========
def send_to_ding(content, link):
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "qiuqiu动态更新",
            "text": f"**🔔 qiuqiu博主新动态**\n\n{content}\n\n[查看原文]({link})"
        }
    }
    try:
        print("🔧 正在发送钉钉...")
        r = requests.post(DING_WEBHOOK, json=message, timeout=10)
        print("钉钉响应码：", r.status_code)
        print("钉钉响应内容：", r.text)
    except Exception as e:
        print("❌ 发送异常：", repr(e))

# ========== 最新API抓取（核心修改） ==========
def fetch_posts():
    if not XUEQIU_USER_ID or not DING_WEBHOOK:
        print("❌ 环境变量缺失")
        return

    # 2026 最新用户动态API
    api_url = f"https://xueqiu.com/v4/statuses/user_timeline.json?user_id={XUEQIU_USER_ID}&page=1&count=20"
    print("🔗 访问API：", api_url)

    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        print("API状态码：", resp.status_code)
        if resp.status_code != 200:
            print("API返回非200，前300字符：", resp.text[:300])
            return
    except Exception as e:
        print("❌ 访问API失败：", repr(e))
        return

    try:
        data = resp.json()
        status_list = data.get("statuses", [])
        print("✅ 抓到动态数量：", len(status_list))
    except Exception as e:
        print("❌ JSON解析失败：", repr(e))
        print("原始响应：", resp.text[:500])
        return

    sent = load_sent_ids()
    print("📌 已发送过的数量：", len(sent))

    for status in status_list:
        sid = str(status.get("id", ""))
        if not sid:
            continue
        if sid in sent:
            print("跳过已发送：", sid)
            continue

        content = status.get("text", "").strip()
        link = f"https://xueqiu.com/statuses/{sid}.html"
        print("✨ 新动态：", sid, content[:50])

        send_to_ding(content, link)
        save_sent_id(sid)

if __name__ == "__main__":
    fetch_posts()
