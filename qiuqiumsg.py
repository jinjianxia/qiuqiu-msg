import time
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 配置（通过环境变量传入） ---
USER_ID = os.environ.get("XUEQIU_USER_ID", "")
CHECK_INTERVAL_SEC = int(os.environ.get("CHECK_INTERVAL_SEC") or "600")
SENDER = os.environ.get("MAIL_SENDER", "")
PASSWORD = os.environ.get("MAIL_PASSWORD", "")
RECEIVER = os.environ.get("MAIL_RECEIVER", MAIL_SENDER)

if not all([USER_ID, SENDER, PASSWORD, RECEIVER]):
    print("[错误] 请设置环境变量: XUEQIU_USER_ID, MAIL_SENDER, MAIL_PASSWORD, MAIL_RECEIVER")
    exit(1)

def send_email(subject, html_content):
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['From'] = SENDER
    msg['To'] = RECEIVER
    msg['Subject'] = Header(subject, 'utf-8')
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, [RECEIVER], msg.as_string())
        server.quit()
        print("[邮件] 发送成功")
    except Exception as e:
        print(f"[错误] 邮件发送失败: {e}")

def fetch_latest_posts():
    session = requests.Session()
    # 模拟真实浏览器，增加获取成功的概率
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://xueqiu.com/u/{USER_ID}"
    }
    
    # 既然你说不需要 Token 也能读，我们先直接请求首页激活 Session
    session.get("https://xueqiu.com/", headers=headers, timeout=10)
    
    api_url = "https://xueqiu.com/v4/statuses/user_timeline.json"
    params = {"user_id": USER_ID, "page": 1, "type": 0}
    
    try:
        res = session.get(api_url, params=params, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("statuses", [])
        else:
            print(f"[错误] API 访问失败，状态码: {res.status_code}")
            return []
    except Exception as e:
        print(f"[错误] 网络异常: {e}")
        return []

def fetch_full_status(session, post_id):
    """获取单条帖子的完整内容（含全文）"""
    url = f"https://xueqiu.com/statuses/show.json?id={post_id}"
    try:
        res = session.get(url, timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[警告] 获取帖子 {post_id} 全文失败: {e}")
    return None


def run():
    now_ms = time.time() * 1000  # 转为毫秒与雪球 JSON 匹配
    interval_ms = CHECK_INTERVAL_SEC * 1000

    statuses = fetch_latest_posts()
    if not statuses:
        print("[提示] 未抓取到内容")
        return

    # 复用 fetch_latest_posts 中的 session
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://xueqiu.com/u/{USER_ID}"
    })
    session.get("https://xueqiu.com/", timeout=10)

    updates = []
    for s in statuses:
        created_at = s.get("created_at", 0)
        edited_at = s.get("edited_at", 0)

        # 提取字段
        post_id = s.get("id")
        title = s.get("title") or ""
        content = s.get("description") or s.get("text") or ""
        target_url = f"https://xueqiu.com{s.get('target')}"
        screen_name = s.get("user", {}).get("screen_name", USER_ID)
        time_before = s.get("timeBefore", "")

        # 元数据
        like_count = s.get("like_count", 0)
        reply_count = s.get("reply_count", 0)
        retweet_count = s.get("retweet_count", 0)
        fav_count = s.get("fav_count", 0)

        # 判断是否在时间窗口内
        time_diff_ms = now_ms - created_at
        is_new = 0 < time_diff_ms <= interval_ms
        is_edited = edited_at and (edited_at > created_at) and (0 < (now_ms - edited_at) <= interval_ms)

        if not (is_new or is_edited):
            continue

        # 只对时间窗口内的帖子获取全文
        if is_new or is_edited:
            detail = fetch_full_status(session, post_id)
            if detail:
                full_text = detail.get("text") or detail.get("description") or content
                if full_text.strip():
                    content = full_text

        if is_new:
            tag = "<span style='color:red;'>【最新发布】</span>"
        else:
            tag = "<span style='color:orange;'>【帖子已修改】</span>"

        # 截取过长的内容，避免邮件过大
        if len(content) > 2000:
            content = content[:2000] + "..."

        # 构建单条动态的 HTML
        title_html = f"<b>{title}</b><br>" if title else ""
        updates.append(f"""
        <div style="padding:12px;border:1px solid #e0e0e0;border-radius:8px;margin-bottom:10px;">
            <div style="margin-bottom:6px;">{tag} {title_html}</div>
            <div style="margin-bottom:8px;line-height:1.6;">{content}</div>
            <div style="font-size:12px;color:#888;">
                {time_before} · 
                赞 {like_count} · 评论 {reply_count} · 转发 {retweet_count} · 收藏 {fav_count}
            </div>
            <div style="margin-top:6px;">
                <a href="{target_url}" style="color:#1a73e8;text-decoration:none;font-size:13px;">查看原文 →</a>
            </div>
        </div>
        """.strip())

    if updates:
        html_body = f"""
        <h3 style="border-left:4px solid #e6162d;padding-left:10px;">🔔 雪球博主 {screen_name} 动态更新</h3>
        """ + "".join(updates)
        send_email(f"雪球更新通知: {screen_name}", html_body)
        print(f"[成功] 检测到 {len(updates)} 条变动")
    else:
        print("[系统] 暂无新消息")

if __name__ == "__main__":
    run()
