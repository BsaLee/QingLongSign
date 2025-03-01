'''
new Env('恩山论坛签到')
cron: 1 0 * * *
Author       : BNDou
Date         : 2022-10-30 22:21:48
LastEditTime: 2024-08-03 20:45:54
FilePath: \Auto_Check_In\checkIn_EnShan.py
Description  : 添加环境变量COOKIE_ENSHAN，多账号用 回车 或 && 分开
'''

import os
import re
import sys
import requests
from lxml import etree
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 获取环境变量
def get_env():
    if "COOKIE_ENSHAN" in os.environ:
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_ENSHAN'))
    else:
        print('未添加COOKIE_ENSHAN变量')
        send('恩山论坛签到', '未添加COOKIE_ENSHAN变量')
        sys.exit(0)

    return cookie_list

def request_with_retry(url, headers, retries=3, delay=5):
    """带重试机制的网络请求"""
    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response
            else:
                print(f"请求失败，状态码: {response.status_code}")
        except requests.RequestException as e:
            print(f"请求错误: {e}")
        time.sleep(delay)
    return None

class EnShan:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_name = None
        self.user_group = None
        self.coin = None
        self.contribution = None
        self.point = None
        self.date = None

    def get_user(self):
        user_url = "https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit"
        headers = {
            'Cookie': self.cookie,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'www.right.com.cn',
            'Pragma': 'no-cache',
            'Referer': 'https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        user_res = request_with_retry(user_url, headers)

        if not user_res:
            print("获取用户信息失败")
            self.user_name = None
            return

        self.user_name = re.findall(r'访问我的空间">(.*?)</a>', user_res.text)[0]
        self.user_group = re.findall(r'用户组: (.*?)</a>', user_res.text)[0]
        self.contribution = re.findall(r'贡献: </em>(.*?) 分', user_res.text)[0]
        self.coin = re.findall(r'恩山币: </em>(.*?) 币', user_res.text)[0]
        self.point = re.findall(r'积分: </em>(.*?) ', user_res.text)[0]

    def get_log(self):
        log_url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog"
        headers = {
            'Cookie': self.cookie,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'www.right.com.cn',
            'Pragma': 'no-cache',
            'Referer': 'https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&suboperation=creditrulelog',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        log_res = request_with_retry(log_url, headers)

        if not log_res:
            print("获取签到记录失败，服务器无响应")
            self.date = None
            return

        html = etree.HTML(log_res.text)

        date_elements = html.xpath('//tr/td[6]/text()')
        if date_elements:
            self.date = date_elements[0]
        else:
            print("未找到签到日期，可能是页面结构已更改")
            self.date = "未知"

    def main(self):
        self.get_log()
        self.get_user()

        if self.user_name and self.date:
            return (
                f'👶{self.user_group}：{self.user_name}\n'
                f'🏅恩山币：{self.coin} 贡献：{self.contribution} 积分：{self.point}\n'
                f'⭐签到成功或今日已签到\n'
                f'⭐最后签到时间：{self.date}')
        else:
            return '❌️签到失败，可能是cookie失效了！'


def send(subject, message):
    """发送邮件"""
    sender_email = "your_email@example.com"
    receiver_email = "receiver@example.com"
    password = "your_email_password"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
        print("邮件已发送")
    except Exception as e:
        print(f"邮件发送失败: {e}")


if __name__ == "__main__":
    print("----------恩山论坛开始尝试签到----------")

    msg, cookie_EnShan = "", get_env()

    i = 0
    while i < len(cookie_EnShan):
        log = f"第 {i + 1} 个账号开始执行任务\n"
        log += EnShan(cookie_EnShan[i]).main()
        msg += log + "\n\n"
        i += 1

    try:
        send('恩山论坛签到', msg)
    except Exception as err:
        print(f'{err}\n❌️错误，请查看运行日志！')

    print("----------恩山论坛签到执行完毕----------")
