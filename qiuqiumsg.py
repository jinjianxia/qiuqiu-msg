import os
import feedparser
import requests

# ========== 从 GitHub Secrets 读取（完全安全，不泄露）==========
RSS_URL = os.getenv("RSS_URL")
DING_WEBHOOK = os.getenv("DING_WEBHOOK")
SEND_HISTORY_PATH = "/tmp/sent_history.txt"

# 本地记录已发送的文章
def load_sent_history():
    try:
        with open(SEND_HISTORY_PATH, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    except:
        return set()

def save_sent_history(h):
    try:
        with open(SEND_HISTORY_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(h))
    except:
        pass

# 推送
def send_to_ding(title, content, link):
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "title": "球球更新",
            "text": f"**🔔 球球博主新动态**\n\n{content}\n\n[查看原文]({link})"
        }
    }
    try:
        requests.post(DING_WEBHOOK, json=msg, timeout=10)
    except:
        pass

# 主逻辑
if __name__ == "__main__":
    sent = load_sent_history()
    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries[:3]:  # 只看最新3条，防刷屏
        article_id = entry.get("id", entry.get("link", ""))
        if article_id and article_id not in sent:
            send_to_ding(entry.title, entry.summary, entry.link)
            sent.add(article_id)

    save_sent_history(sent)