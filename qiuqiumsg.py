import os
import requests

print("=== 脚本开始运行 ===")

# 直接读取 Secrets
webhook = os.getenv("DING_WEBHOOK")
print("Webhook 是否存在:", bool(webhook))

# 强制发一条最简单的消息
def test():
    data = {
        "msgtype": "text",
        "text": {
            "content": "雪球测试"
        }
    }
    resp = requests.post(webhook, json=data)
    print("发送状态码:", resp.status_code)
    print("返回结果:", resp.text)

test()
print("=== 脚本结束 ===")
