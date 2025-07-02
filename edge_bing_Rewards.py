    # name: "edge刷积分"
    # cron: 55 0,8,14,19 * * *
    # 更新时间:2025-07-01
    # 将多个账号的cookie按行分隔设置到 pc_cookies 和 mobile_cookies 变量


import requests
import random
import re
import time
import json
import os
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs

def print_log(title: str, msg: str):
    """打印带时间戳的日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} [{title}]: {msg or ''}")

# 从环境变量获取cookie，支持多行（一行一个）
def get_cookies():
    """从环境变量获取cookie，支持多行（一行一个）"""
    # 获取电脑端cookie
    pc_env_cookies = os.getenv("pc_cookies")
    # 获取移动端cookie
    mobile_env_cookies = os.getenv("mobile_cookies")
    
    pc_cookies_list = []
    mobile_cookies_list = []
    
    if pc_env_cookies:
        # 分割多行cookie，去除空行和空白字符
        pc_cookies_list = [ck.strip() for ck in pc_env_cookies.strip().split("\n") if ck.strip()]
    
    if mobile_env_cookies:
        # 分割多行cookie，去除空行和空白字符
        mobile_cookies_list = [ck.strip() for ck in mobile_env_cookies.strip().split("\n") if ck.strip()]
    
    # 检查cookie数量是否匹配
    if len(pc_cookies_list) != len(mobile_cookies_list):
        print_log("配置错误", f"电脑端cookie数量({len(pc_cookies_list)})与移动端cookie数量({len(mobile_cookies_list)})不匹配")
        return [], []
    
    if not pc_cookies_list and not mobile_cookies_list:
        print_log("配置错误", "未配置 pc_cookies 和 mobile_cookies 环境变量，无法执行任务")
        return [], []
    
    return pc_cookies_list, mobile_cookies_list

# 获取cookie列表
pc_cookies_list, mobile_cookies_list = get_cookies()
if not pc_cookies_list or not mobile_cookies_list:
    print_log("启动错误", "没有可用的cookie，程序退出")
    exit(1)

print_log("初始化", f"检测到 {len(pc_cookies_list)} 个账号，即将开始...")

# 浏览器通用头部（将在运行时根据当前cookie动态设置）
BROWSER_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "referer": "https://rewards.bing.com/"
}

def get_rewards_points(cookies):
    """查询当前积分和账号信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; OPPO R11 Plus Build/PKQ1.190414.001; ) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 BingSapphire/31.4.2110003555',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'X-Search-Location': 'lat=19.3516,long=110.1012,re=-1.0000,disp=%20',
        'Sapphire-OSVersion': '9',
        'Sapphire-Configuration': 'Production',
        'Sapphire-APIVersion': '114',
        'Sapphire-Market': 'zh-CN',
        'X-Search-ClientId': '2E2936301F8D6BFD3225203D1E5F6A0D',
        'Sapphire-DeviceType': 'OPPO R11 Plus',
        'X-Requested-With': 'com.microsoft.bing',
        'Cookie': cookies
    }

    url = 'https://rewards.bing.com/'
    params = {
        'ssp': '1',
        'safesearch': 'moderate',
        'setlang': 'zh-hans',
        'cc': 'CN',
        'ensearch': '0',
        'PC': 'SANSAAND'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        content = response.text
        
        # 提取积分
        points_pattern = r'"availablePoints":(\d+)'
        points_match = re.search(points_pattern, content)
        
        # 提取邮箱账号
        email_pattern = r'email:\s*"([^"]+)"'
        email_match = re.search(email_pattern, content)
        
        available_points = None
        email = None
        
        if points_match:
            available_points = int(points_match.group(1))
            # print_log("积分查询", f"当前积分: {available_points}")
        else:
            print_log("积分查询", "未找到 availablePoints 值")
            
        if email_match:
            email = email_match.group(1)
            # print_log("账号信息", f"账号: {email}")
        else:
            print_log("账号信息", "未找到 email 值")
            
        return {
            'points': available_points,
            'email': email
        }
            
    except requests.exceptions.RequestException as e:
        print_log("积分查询", f"请求失败: {e}")
        return None
    except Exception as e:
        print_log("积分查询", f"发生错误: {e}")
        return None

def bing_search_pc(cookies):
    # 随机生成两个汉字
    hanzi_range = list(range(0x4e00, 0x9fa6))
    q = chr(random.choice(hanzi_range)) + chr(random.choice(hanzi_range))

    url = "https://cn.bing.com/search"
    params = {
        "q": q,
        "qs": "FT",
        "form": "TSASDS"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Referer": "https://rewards.bing.com/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": cookies
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print_log("电脑搜索", f"电脑搜索异常: {e}")
        return False

def bing_search_mobile(cookies):
    """执行移动设备搜索（来自bing_search.py）"""
    # 随机生成两个汉字
    q = ''.join(chr(random.randint(0x4e00, 0x9fa5)) for _ in range(2))

    url = "https://cn.bing.com/search"
    params = {
        "q": q,
        "form": "NPII01",
        "filters": "tnTID:\"DSBOS_F29F59C848FA467D96D2F8EEC96FBC7A\" tnVersion:\"8908b7744161474e8812c12c507ece49\" Segment:\"popularnow.carousel\" tnCol:\"39\" tnScenario:\"TrendingTopicsAPI\" tnOrder:\"ef45722b-8213-4953-9c44-57e0dde6ac78\"",
        "ssp": "1",
        "safesearch": "moderate",
        "setlang": "zh-hans",
        "cc": "CN",
        "ensearch": "0",
        "PC": "SANSAAND"
    }

    headers = {
        "host": "cn.bing.com",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; OPPO R11 Plus Build/PKQ1.190414.001; ) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 BingSapphire/31.4.2110003555",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "x-search-location": "lat=19.3516,long=110.1012,re=-1.0000,disp=%20",
        "sapphire-osversion": "9",
        "sapphire-configuration": "Production",
        "sapphire-apiversion": "114",
        "sapphire-market": "zh-CN",
        "x-search-clientid": "2E2936301F8D6BFD3225203D1E5F6A0D",
        "sapphire-devicetype": "OPPO R11 Plus",
        "accept-encoding": "gzip, deflate",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": cookies,
        "x-requested-with": "com.microsoft.bing"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print_log("移动搜索", f"移动设备搜索异常: {e}")
        return False

def check_points_increase(initial_points, current_points):
    """检查积分是否增加"""
    if initial_points is None or current_points is None:
        return False
    return current_points > initial_points

def get_current_timestamp():
    """获取当前时间戳（13位，毫秒）"""
    return int(time.time() * 1000)

def get_dashboard_data(cookies):
    """统一获取dashboard数据和token"""
    try:
        headers = {
            **BROWSER_HEADERS,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "cookie": cookies
        }
        resp = requests.get("https://rewards.bing.com/", headers=headers, timeout=30)
        resp.raise_for_status()
        
        html_text = resp.text
        token_match = re.search(r'name="__RequestVerificationToken".*?value="([^"]+)"', html_text)
        dashboard_match = re.search(r'var dashboard\s*=\s*(\{.*?\});', html_text, re.DOTALL)
        
        if not token_match:
            print_log('Dashboard错误', "未能获取 __RequestVerificationToken")
            return None
        
        if not dashboard_match:
            print_log('Dashboard错误', "未能获取 dashboard 数据")
            return None
        
        token = token_match.group(1)
        dashboard_json = json.loads(dashboard_match.group(1).rstrip().rstrip(';'))
        
        return {
            'dashboard_data': dashboard_json,
            'token': token
        }
    except Exception as e:
        print_log('Dashboard错误', str(e))
        return None

def complete_daily_set_tasks(pc_cookies, mobile_cookies):
    """完成每日活动任务，失败时自动切换到移动端cookie重试"""
    completed_count = 0
    
    # 首先尝试使用电脑端cookie
    print_log("每日活动", "--- 使用电脑端cookie执行每日活动任务 ---")
    result = _complete_daily_set_tasks_internal(pc_cookies)
    completed_count += result['completed']
    
    # 如果有失败的任务，使用移动端cookie重试
    if result['failed_tasks']:
        print_log("每日活动", f"--- 使用移动端cookie重试 {len(result['failed_tasks'])} 个失败任务 ---")
        retry_result = _complete_daily_set_tasks_internal(mobile_cookies, result['failed_tasks'])
        completed_count += retry_result['completed']
        
        if retry_result['failed_tasks']:
            print_log("每日活动", f"⚠️ 仍有 {len(retry_result['failed_tasks'])} 个任务失败")
    
    return completed_count

def _complete_daily_set_tasks_internal(cookies, specific_tasks=None):
    """内部函数：完成每日活动任务"""
    completed_count = 0
    failed_tasks = []
    
    try:
        # 获取dashboard数据
        dashboard_result = get_dashboard_data(cookies)
        if not dashboard_result:
            return {'completed': completed_count, 'failed_tasks': failed_tasks}
        
        dashboard_data = dashboard_result['dashboard_data']
        token = dashboard_result['token']
        
        # 提取积分信息
        if 'userStatus' in dashboard_data:
            user_status = dashboard_data['userStatus']
            available_points = user_status.get('availablePoints', 0)
            lifetime_points = user_status.get('lifetimePoints', 0)
            print_log("每日活动", f"✅ 当前积分: {available_points}, 总积分: {lifetime_points}")
        
        # 提取每日任务
        today_str = date.today().strftime('%m/%d/%Y')
        daily_tasks = dashboard_data.get('dailySetPromotions', {}).get(today_str, [])
        
        if not daily_tasks:
            print_log("每日活动", "没有找到今日的每日活动任务")
            return {'completed': completed_count, 'failed_tasks': failed_tasks}
        
        # 过滤未完成的任务
        if specific_tasks:
            # 如果指定了特定任务，使用指定的任务列表
            incomplete_tasks = specific_tasks
        else:
            # 否则过滤未完成的任务
            incomplete_tasks = [task for task in daily_tasks if not task.get('complete')]
        
        if not incomplete_tasks:
            print_log("每日活动", "所有每日活动任务已完成")
            return {'completed': completed_count, 'failed_tasks': failed_tasks}
        
        print_log("每日活动", f"找到 {len(incomplete_tasks)} 个未完成的每日活动任务")
        
        # 执行任务
        for i, task in enumerate(incomplete_tasks, 1):
            print_log("每日活动", f"执行任务 {i}/{len(incomplete_tasks)}: {task.get('title', '未知任务')}")
            
            if execute_task(task, token, cookies):
                completed_count += 1
                print_log("每日活动", f"✅ 任务完成: {task.get('title', '未知任务')}")
            else:
                print_log("每日活动", f"❌ 任务失败: {task.get('title', '未知任务')}")
                failed_tasks.append(task)
            
            # 随机延迟
            time.sleep(random.uniform(2, 4))
        
        print_log("每日活动", f"每日活动执行完成，成功完成 {completed_count} 个任务")
        
    except Exception as e:
        print_log('每日活动出错', f"异常: {e}")
    
    return {'completed': completed_count, 'failed_tasks': failed_tasks}

def setup_task_headers(cookies):
    """设置任务执行的请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Ch-Ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Platform-Version': '"19.0.0"',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Bitness': '"64"',
        'Sec-Ch-Prefers-Color-Scheme': 'light',
        'Sec-Ms-Gec': '1',
        'Sec-Ms-Gec-Version': '1-137.0.3296.83',
        'Cookie': cookies
    }
    return headers

def setup_api_headers(cookies):
    """设置API请求的请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://rewards.bing.com',
        'Referer': 'https://rewards.bing.com/',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Ch-Ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Platform-Version': '"19.0.0"',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Bitness': '"64"',
        'Sec-Ch-Prefers-Color-Scheme': 'light',
        'Sec-Ms-Gec': '1',
        'Sec-Ms-Gec-Version': '1-137.0.3296.83',
        'Cookie': cookies
    }
    return headers

def extract_tasks(more_promotions):
    """提取任务"""
    tasks = []
    for promotion in more_promotions:
        priority = promotion.get('priority')
        complete = promotion.get('complete')
        promotion_type = promotion.get('promotionType')
        # 检查是否被锁定
        locked_status = promotion.get('exclusiveLockedFeatureStatus')
        if priority == 0 and complete == False and locked_status != 'locked':
            tasks.append(promotion)
    if not tasks:
        for promotion in more_promotions:
            priority = promotion.get('priority')
            complete = promotion.get('complete')
            promotion_type = promotion.get('promotionType')
            locked_status = promotion.get('exclusiveLockedFeatureStatus')
            if (priority == 1 and complete == False and promotion_type == 'urlreward' and locked_status != 'locked'):
                tasks.append(promotion)
    
    # 继续查找priority=7的任务，不管前面是否找到了其他优先级的任务
    for promotion in more_promotions:
        priority = promotion.get('priority')
        complete = promotion.get('complete')
        promotion_type = promotion.get('promotionType')
        locked_status = promotion.get('exclusiveLockedFeatureStatus')
        if (priority == 7 and complete == False and promotion_type == 'urlreward' and locked_status != 'locked'):
            tasks.append(promotion)
    
    return tasks

def extract_search_query(destination_url):
    """从URL中提取搜索查询"""
    try:
        parsed_url = urlparse(destination_url)
        query_params = parse_qs(parsed_url.query)
        if 'q' in query_params:
            search_query = query_params['q'][0]
            import urllib.parse
            search_query = urllib.parse.unquote(search_query)
            return search_query
        return None
    except Exception as e:
        print_log("更多活动", f"提取搜索查询失败: {e}")
        return None

def report_activity(task, token, cookies):
    """报告任务活动，真正完成任务"""
    if not token:
        print_log("更多活动", "❌ 缺少RequestVerificationToken，无法报告活动")
        return False
    
    try:
        post_url = 'https://rewards.bing.com/api/reportactivity?X-Requested-With=XMLHttpRequest'
        post_headers = setup_api_headers(cookies)
        
        payload = f"id={task['name']}&hash={task.get('hash', '')}&timeZone=480&activityAmount=1&dbs=0&form=&type=&__RequestVerificationToken={token}"
        
        response = requests.post(post_url, data=payload, headers=post_headers, timeout=15)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("activity") and result["activity"].get("points", 0) > 0:
                    print_log("更多活动", f"✅ 获得{result['activity']['points']}积分")
                    return True
                else:
                    print_log("更多活动", f"⚠️ 未获得积分")
                    return False
            except json.JSONDecodeError:
                print_log("更多活动", f"⚠️ 活动报告返回内容无法解析")
                return False
        else:
            print_log("更多活动", f"❌ 活动报告请求失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_log("更多活动", f"❌ 报告活动时出错: {e}")
        return False

def execute_task(task, token, cookies):
    """执行单个任务"""
    try:
        destination_url = task.get('destinationUrl') or task.get('attributes', {}).get('destination')
        if not destination_url:
            print_log("更多活动", f"❌ 任务 {task.get('name')} 没有目标URL")
            return False
        
        # 检查是否为搜索任务
        search_query = extract_search_query(destination_url)
        
        if search_query:
            # 搜索任务
            print_log("更多活动", f"🔍 执行搜索任务: {task.get('title')}")
        else:
            # 非搜索任务（如Edge相关任务）
            print_log("更多活动", f"🌐 执行URL访问任务: {task.get('title')}")
            
            # 对于Edge相关任务，可能需要特殊处理URL
            if 'microsoftedgewelcome.microsoft.com' in destination_url:
                # 转换为实际的Microsoft URL
                if 'focus=privacy' in destination_url:
                    destination_url = 'https://www.microsoft.com/zh-cn/edge/welcome?exp=e155&form=ML23ZX&focus=privacy&cs=2175697442'
                elif 'focus=performance' in destination_url:
                    destination_url = 'https://www.microsoft.com/zh-cn/edge/welcome?exp=e155&form=ML23ZX&focus=performance&cs=2175697442'
        
        # 设置任务执行请求头
        headers = setup_task_headers(cookies)
        
        # 发送请求
        response = requests.get(
            destination_url, 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            print_log("更多活动", f"✅ 任务执行成功")
            # 报告活动
            if report_activity(task, token, cookies):
                return True
            else:
                print_log("更多活动", f"⚠️ 任务执行成功但活动报告失败")
                return False
        else:
            print_log("更多活动", f"❌ 任务执行失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print_log("更多活动", f"❌ 执行任务时出错: {e}")
        return False

def complete_more_activities(pc_cookies, mobile_cookies):
    """完成更多活动任务，失败时自动切换到移动端cookie重试"""
    completed_count = 0
    
    # 首先尝试使用电脑端cookie
    print_log("更多活动", "--- 使用电脑端cookie执行更多活动任务 ---")
    result = _complete_more_activities_internal(pc_cookies)
    completed_count += result['completed']
    
    # 如果有失败的任务，使用移动端cookie重试
    if result['failed_tasks']:
        print_log("更多活动", f"--- 使用移动端cookie重试 {len(result['failed_tasks'])} 个失败任务 ---")
        retry_result = _complete_more_activities_internal(mobile_cookies, result['failed_tasks'])
        completed_count += retry_result['completed']
        
        if retry_result['failed_tasks']:
            print_log("更多活动", f"⚠️ 仍有 {len(retry_result['failed_tasks'])} 个任务失败")
    
    return completed_count

def _complete_more_activities_internal(cookies, specific_tasks=None):
    """内部函数：完成更多活动任务"""
    completed_count = 0
    failed_tasks = []
    
    try:
        # 获取dashboard数据
        dashboard_result = get_dashboard_data(cookies)
        if not dashboard_result:
            print_log("更多活动", "无法获取dashboard数据，跳过更多活动\n")
            return {'completed': completed_count, 'failed_tasks': failed_tasks}
        
        dashboard_data = dashboard_result['dashboard_data']
        token = dashboard_result['token']
        
        # 提取积分信息
        if 'userStatus' in dashboard_data:
            user_status = dashboard_data['userStatus']
            available_points = user_status.get('availablePoints', 0)
            lifetime_points = user_status.get('lifetimePoints', 0)
            print_log("更多活动", f"✅ 当前积分: {available_points}, 总积分: {lifetime_points}")
        
        # 提取更多活动任务
        if specific_tasks:
            # 如果指定了特定任务，使用指定的任务列表
            tasks = specific_tasks
        else:
            # 否则从dashboard数据中提取任务
            more_promotions = dashboard_data.get('morePromotions', [])
            tasks = extract_tasks(more_promotions)
        
        if not tasks:
            print_log("更多活动", "没有找到可执行的更多活动任务\n")
            return {'completed': completed_count, 'failed_tasks': failed_tasks}
        
        print_log("更多活动", f"找到 {len(tasks)} 个可执行的更多活动任务")
        
        # 执行任务
        for i, task in enumerate(tasks, 1):
            print_log("更多活动", f"执行任务 {i}/{len(tasks)}: {task.get('title', '未知任务')}")
            
            if execute_task(task, token, cookies):
                completed_count += 1
                print_log("更多活动", f"✅ 任务完成: {task.get('title', '未知任务')}")
            else:
                print_log("更多活动", f"❌ 任务失败: {task.get('title', '未知任务')}")
                failed_tasks.append(task)
            
            # 随机延迟
            time.sleep(random.uniform(2, 4))
        
        print_log("更多活动", f"更多活动执行完成，成功完成 {completed_count} 个任务\n")
        
    except Exception as e:
        print_log('更多活动出错', f"异常: {e}\n")
    
    return {'completed': completed_count, 'failed_tasks': failed_tasks}

def perform_search_tasks(search_type, search_func, max_count, initial_points, cookies, check_interval=3):
    """执行搜索任务的通用函数"""
    print_log(search_type, f"--- 开始执行{max_count}次{search_type} ---")
    count = 0
    last_check_points = initial_points
    
    for i in range(max_count):
        count += 1
        
        if search_func(cookies):
            delay = random.randint(15, 30)
            print_log(search_type, f"第 {count} 次{search_type}成功，等待 {delay} 秒...")
            time.sleep(delay)
        else:
            print_log(search_type, f"第 {count} 次{search_type}失败")
        
        # 每check_interval次检查积分
        if count % check_interval == 0:
            current_data = get_rewards_points(cookies)
            if current_data and current_data['points']:
                if check_points_increase(last_check_points, current_data['points']):
                    print_log("积分变化", f"--- 检查积分变化，积分已增加: {last_check_points} -> {current_data['points']}")
                    last_check_points = current_data['points']
                else:
                    print_log("积分变化", f"--- 检查积分变化，积分未增加，停止搜索")
                    break
            else:
                print_log("积分查询", "无法获取当前积分")
                break
    if count == 3:
        count = 0
    return count

def single_account_main(pc_cookies, mobile_cookies, account_index):
    """单个账号的完整任务流程"""
    print(f"\n{'='*15} [开始处理账号 {account_index}] {'='*15}")
    
    # 1. 查询初始积分和账号信息（使用电脑端cookie查询）
    print_log("账号信息", "---查询账号信息和初始积分 ---")
    initial_data = get_rewards_points(pc_cookies)
    if initial_data is None or initial_data['points'] is None:
        print_log("账号信息", "无法获取初始积分，跳过此账号")
        return None
    
    script_start_points = initial_data['points']
    email = initial_data.get('email', '未知邮箱')
    print_log("账号信息", f"账号: {email}, 初始积分: {script_start_points}")
    
    # 2. 执行电脑搜索（使用电脑端cookie）
    pc_count = perform_search_tasks("电脑搜索", bing_search_pc, 30, script_start_points, pc_cookies)
    
    # 获取电脑搜索完成后的积分，作为移动搜索的基准
    pc_completed_points = get_rewards_points(pc_cookies)
    mobile_start_points = pc_completed_points['points'] if pc_completed_points else script_start_points
    
    # 3. 执行移动设备搜索（使用移动端cookie）
    mobile_count = perform_search_tasks("移动搜索", bing_search_mobile, 20, mobile_start_points, mobile_cookies)
    
    # 4. 执行每日活动任务（支持重试机制）
    print_log("每日活动", "--- 开始执行每日活动任务 ---")
    daily_tasks_completed = complete_daily_set_tasks(pc_cookies, mobile_cookies)
    
    # 5. 执行更多活动任务（支持重试机制）
    print_log("更多活动", "--- 开始执行更多活动任务 ---")
    more_activities_completed = complete_more_activities(pc_cookies, mobile_cookies)
    
    # 6. 最终积分查询（使用电脑端cookie）
    final_data = get_rewards_points(pc_cookies)
    
    if final_data and final_data['points'] is not None:
        final_points = final_data['points']
        points_earned = final_points - script_start_points
        print_log("脚本完成", f"最终积分: {final_points} (+{points_earned})")
        
        # 打印账号总结
        print(f"\n{'='*10} [账号 {account_index} 任务完成] {'='*10}")
        print(f"账号: {email}")
        print(f"✨ 积分变化: {script_start_points} -> {final_points} (+{points_earned})")
        print(f"✨ 电脑搜索: {pc_count} 次")
        print(f"✨ 移动搜索: {mobile_count} 次")
        print(f"✨ 每日活动: {daily_tasks_completed} 个")
        print(f"✨ 更多活动: {more_activities_completed} 个")
        print("="*50)
        
        return True
    else:
        print_log("脚本完成", "无法获取最终积分")
        return False

def main():
    """主函数 - 支持多账号执行"""
    successful_accounts = 0
    
    for i in range(len(pc_cookies_list)):
        try:
            pc_cookies = pc_cookies_list[i]
            mobile_cookies = mobile_cookies_list[i]
            
            if single_account_main(pc_cookies, mobile_cookies, i + 1):
                successful_accounts += 1
            
            # 账号间延迟（除了最后一个账号）
            if i < len(pc_cookies_list) - 1:
                wait_time = random.randint(20, 40)
                print_log("账号切换", f"等待 {wait_time}s 后继续...")
                time.sleep(wait_time)
                
        except Exception as e:
            print_log(f"账号{i+1}错误", f"处理账号时发生异常: {e}")
            continue
    
    # 最终总结
    print(f"\n\n{'='*10} [全部任务完成] {'='*10}")
    print_log("任务总结", f"成功处理 {successful_accounts}/{len(pc_cookies_list)} 个账号")

if __name__ == "__main__":
    main() 
