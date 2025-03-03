
    # name: "小米运动"
    # cron: 0 8 * * *
    # 更新时间:2025-03-03
    # 环境变量中设置xiaomi_yundong = user password;user2 password2
    # 支持多账号,用;分隔


import requests
import random
import os
import time

def get_accounts():
    accounts = os.getenv("xiaomi_yundong", "")
    if not accounts:
        print("环境变量 xiaomi_yundong 未设置")
        return []
    
    account_list = []
    for acc in accounts.split(";"):
        parts = acc.split(" ")
        if len(parts) == 2:
            account_list.append({"user": parts[0], "password": parts[1]})
        else:
            print(f"账号格式错误: {acc}")
    
    return account_list

def update_steps(user, password):
    """ 发送步数更新请求 """
    step = random.randint(33333, 65213)
    params = {
        'user': user,
        'password': password,
        'step': step,
    }
    
    url = "https://api.leafone.cn/api/misport"
    response = requests.post(url, params=params).json()
    print(f"账号 {user} 提交步数 {step}，返回: {response.get('msg', '无返回消息')}")
    if 'data' in response and 'step' in response['data']:
        print(f"实际步数: {response['data']['step']}")

if __name__ == "__main__":
    accounts = get_accounts()
    for account in accounts:
        update_steps(account["user"], account["password"])
        time.sleep(10)  # 每次请求后睡眠 5 秒
