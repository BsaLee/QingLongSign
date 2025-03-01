
    # name: "塔斯汀兑换"
    # cron 58 9,16 * * *
    # 更新时间:2025-03-01
    # 青龙环境变量tasitingsign=手机号 user-token;手机号 user-token 和塔斯汀签到共用变量
import requests
import json
import re
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import os



def t(h):    
    date = datetime.now()
    date_zero = datetime.now().replace(year=date.year, month=date.month, day=date.day, hour=h, minute=59, second=59)
    date_zero_time = int(time.mktime(date_zero.timetuple()))
    return date_zero_time

def process_account(account, debug=False):
    phone = account.get('phone')
    user_token = account.get('user-token')
    if not phone or not user_token:
        print(f"账号{account}信息不完整，跳过此账号。")
        return

    account_headers = headers.copy()
    account_headers['user-token'] = user_token

    # 获取账号积分
    point_url = "https://sss-web.tastientech.com/api/wx/point/myPoint"
    point_payload = json.dumps({})
    account_headers['Content-Length'] = str(len(point_payload))
    response = requests.post(point_url, headers=account_headers, data=point_payload)

    if response.status_code != 200:
        print(f"账号{phone}获取积分信息失败")
        return

    point_result = response.json()
    if point_result.get("code") != 200:
        print(f"账号{phone}获取积分信息失败")
        return

    points = point_result.get("result", {}).get("point", 0)
    print(f"账号{phone}当前剩余{points}个积分。")

    if points < 5:
        print(f"账号{phone}积分不足5点，跳过领取")
        return

    # 获取活动列表
    point_url = "https://sss-web.tastientech.com/api/wx/point/coupon/activity/queryAppletActivityList"
    point_payload = json.dumps({
        "activityId": "322"  # 使用一个活动ID来获取列表
    })
    account_headers['Content-Length'] = str(len(point_payload))
    response = requests.post(point_url, headers=account_headers, data=point_payload).json()

    for i in response['result'][0]['activities']:
        if '秒杀' not in i["name"]:
            continue
            
        if '香辣鸡腿中国汉堡' in i["name"] or '粗薯' in i["name"]:
            jp["9"][i["name"]] = {
                "id": i["id"],
                "name": i["name"],
                "openTime": i["timeActivityInfo"][0]["openTime"]
            }
        elif '指定饮品券' in i["name"] or '塔塔鸡块' in i["name"]:
            jp["16"][i["name"]] = {
                "id": i["id"], 
                "name": i["name"],
                "openTime": i["timeActivityInfo"][0]["openTime"]
            }

    # 根据当前时间决定领取哪个时段的活动
    current_hour = datetime.now().hour
    target_activities = {}
    target_hour = None
    if current_hour < 12:  # 上午执行
        target_activities = jp["9"]
        target_hour = 9
    elif current_hour >= 12:  # 下午执行
        target_activities = jp["16"]
        target_hour = 16

    # 为每个目标活动创建订单
    attempt_count = 0
    wt = t(target_hour)
    current_time = time.time()
    
    # 如果距离开始时间超过20分钟，退出脚本
    if not debug and wt - current_time > 1200:  # 1200秒 = 20分钟
        print(f"距离活动开始还有超过20分钟，退出脚本")
        return
        
    # 剔除黑名单中的活动
    target_activities = {k: v for k, v in target_activities.items() if v["id"] not in blacklist_ids}
    
    while attempt_count < max_attempts:
        if debug:
            # 调试模式，直接执行领取逻辑
            for activity in target_activities.values():
                point_url = "https://sss-web.tastientech.com/api/c/pointOrder/create"
                point_payload = json.dumps({
                    "activityId": activity["id"],
                    "requestId": f"{int(time.time()*1000)}"
                })
                response = requests.post(point_url, headers=account_headers, data=point_payload).json()
                error_code = str(response.get('code'))
                error_msg = errcode.get(error_code, response)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] 账号 {phone} - 第 {attempt_count + 1} 次尝试领取 {activity['name']} 结果:", error_msg)
        else:
            # 非调试模式，等待到达指定时间
            if time.time() < wt:
                time.sleep(0.1)
                continue
                
            # 时间到达后执行领取逻辑
            for activity in target_activities.values():
                point_url = "https://sss-web.tastientech.com/api/c/pointOrder/create"
                point_payload = json.dumps({
                    "activityId": activity["id"],
                    "requestId": f"{int(time.time()*1000)}"
                })
                response = requests.post(point_url, headers=account_headers, data=point_payload).json()
                error_code = str(response.get('code'))
                error_msg = errcode.get(error_code, response)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] 账号 {phone} - 第 {attempt_count + 1} 次尝试领取 {activity['name']} 结果:", error_msg)
        
        attempt_count += 1
        time.sleep(0.5)  # 避免请求过于频繁

if __name__ == "__main__":
    # 从青龙环境变量读取
    tasitingsign = os.getenv("tasitingsign")  # 获取青龙变量 tasitingsign
    if not tasitingsign:
        print("没有找到青龙环境变量tasitingsign.")
        exit()

    # 处理tasitingsign变量，按;分割每个账号，账号之间用;分隔
    accounts = []
    for account_str in tasitingsign.split(";"):
        parts = account_str.split()
        if len(parts) != 2:
            print(f"警告：账号字符串 '{account_str}' 格式不正确，跳过此账号。")
            continue
        phone, user_token = parts
        accounts.append({
            "phone": phone,
            "user-token": user_token
        })

    if not accounts:
        print("没有找到有效的账号信息.")
        exit()

    jp = {"9": {}, "16": {}, "20": {}} 

    # 错误码映射
    errcode = {
        "500": "当前活动还未到开放时段!",
        "200": "领取成功"
    }

    # 黑名单ID列表 [286,322]
    blacklist_ids = [322,296]

    # 最大领取次数
    max_attempts = 5

    # 请求头配置
    headers = {
        'Content-Type': 'application/json',
        'version': '3.2.3',
        'xweb_xhr': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c11)XWEB/11581',
        'channel': '1',
        'accept': '*/*',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://servicewechat.com/wx557473f23153a429/376/page-frame.html',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9'
    }

    # 调试模式开关
    debug_mode = False

    # 使用线程池并发处理所有账号
    with ThreadPoolExecutor(max_workers=len(accounts)) as executor:
        executor.map(lambda acc: process_account(acc, debug_mode), accounts)
