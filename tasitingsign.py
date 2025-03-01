
    # name: "塔斯汀签到"
    # cron: 0 0,8 * * *
    # 更新时间:2025-03-01
    # 青龙环境变量tasitingsign=手机号 user-token;手机号 user-token 和塔斯汀兑换共用变量

import requests
import json
import re
import os


# 从青龙环境变量读取
tasitingsign = os.getenv("tasitingsign")  # 获取青龙变量 tasitingsign
if not tasitingsign:
    print("没有找到青龙环境变量tasitingsign.")
    exit()

# 处理tasitingsign变量，按;分割每个账号，账号之间用;分隔
accounts = []
for account_str in tasitingsign.split(";"):
    # 确保每个账号字符串有两个部分
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

headers = {
    'Content-Type': 'application/json',
    'version': '3.2.1',
    'xweb_xhr': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090551)XWEB/11529',
    'channel': '1',
    'accept': '*/*',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://servicewechat.com/wx557473f23153a429/376/page-frame.html',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9'
}

for account in accounts:
    phone = account.get('phone')
    user_token = account.get('user-token')
    if not phone or not user_token:
        print(f"账号{account}信息不完整，跳过此账号。")
        continue

    banner_url = "https://sss-web.tastientech.com/api/minic/shop/intelligence/banner/c/list"
    payload = json.dumps({"phone": phone})
    headers['Content-Length'] = str(len(payload))
    headers['user-token'] = user_token
    response = requests.post(banner_url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f"账号{phone}获取签到活动ID失败，HTTP状态码: {response.status_code}, 错误信息: {response.text}，此账号跳过")
        continue

    result = response.json()
    if result.get("code") != 200:
        print(f"账号{phone}获取签到活动ID失败，返回错误码: {result.get('code')}，错误信息: {result.get('msg')}，此账号跳过")
        continue

    banner = next((item for item in result.get("result", []) if item.get("bannerName") == "每日签到"), None)
    if not banner:
        print(f"账号{phone}未找到每日签到活动，跳过此账号")
        continue

    jump_para = banner.get("jumpPara", "")
    match = re.search(r'activityId%2522%253A(\d+)%257D', jump_para)
    if match:
        activity_id = match.group(1)
    else:
        print(f"账号{phone}未找到签到活动ID，跳过此账号")
        continue

    sign_url = "https://sss-web.tastientech.com/api/sign/member/signV2"
    sign_payload = json.dumps({
        "activityId": activity_id,
        "memberName": "",
        "memberPhone": phone
    })
    headers['Content-Length'] = str(len(sign_payload))
    response = requests.post(sign_url, headers=headers, data=sign_payload)

    if response.status_code != 200:
        print(f"账号{phone}签到失败，HTTP状态码: {response.status_code}, 错误信息: {response.text}，此账号跳过")
        continue

    sign_result = response.json()
    if sign_result.get("code") != 200:
        print(f"账号{phone}签到失败，返回错误码: {sign_result.get('code')}，错误信息: {sign_result.get('msg')}，此账号跳过")
        continue

    reward_info_list = sign_result.get("result", {}).get("rewardInfoList", [])
    if reward_info_list:
        print(f"账号{phone}签到成功：")
        for reward in reward_info_list:
            reward_type = reward.get("rewardType")
            reward_name = reward.get("rewardName")
            if reward_type == 1:
                print(f"得到优惠券【{reward_name}】")
            elif reward_type == 2:
                print(f"得到积分【{reward_name}】")
            else:
                print(f"得到未知奖励【{reward_name}】")
                # 打印未知奖励
                print(f"账号{phone}获得了未知奖励: {reward_name}")

    else:
        print(f"账号{phone}签到成功，但没有得到奖励。")

    point_url = "https://sss-web.tastientech.com/api/wx/point/myPoint"
    point_payload = json.dumps({})
    headers['Content-Length'] = str(len(point_payload))
    response = requests.post(point_url, headers=headers, data=point_payload)

    if response.status_code != 200:
        print(f"账号{phone}获取积分信息失败，HTTP状态码: {response.status_code}, 错误信息: {response.text}")
        continue

    point_result = response.json()
    if point_result.get("code") != 200:
        print(f"账号{phone}获取积分信息失败，返回错误码: {point_result.get('code')}，错误信息: {point_result.get('msg')}")
        continue

    points = point_result.get("result", {}).get("point", 0)
    print(f"账号{phone}当前剩余{points}个积分。")
