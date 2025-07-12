#!/usr/bin/env python3
    # name: "0点电信权益"
    # cron: 55 23 * * *
    # 更新时间:2025-07-010
    # 设置变量chinaTelecomAccount
import os
import re
import sys
import ssl
import time
import json
import execjs
import base64
import random
import certifi
import aiohttp
import asyncio
import datetime
import requests
from requests.adapters import HTTPAdapter
import binascii
import hashlib  # 新增：用于计算MD5
# from lxml import etree  # 未使用的导入，注释掉
from http import cookiejar
from Crypto.Cipher import AES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from aiohttp import ClientSession, TCPConnector
from concurrent.futures import ThreadPoolExecutor
import subprocess



# 彩色输出定义
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ASCII艺术图标
LOGO = f'''
{Color.OKBLUE}
  _____       _           _   _                 _             
 |_   _|____ | | ___  ___| |_| |__   ___  _ __ | |_ ___  _ __ 
   | |/ _ \\\\ \\| |/ _ \\/ __| __| '_ \\ / _ \\| '_ \\| __/ _ \\| '__|
   | |  __/ \\ V |  __/\\__ \\ |_| | | | (_) | | | | || (_) | |   
   |_|\\___|  |_|\\___||___/\\__|_| |_|\\___/|_| |_|\\__\\___/|_|   
{Color.ENDC}
{Color.OKGREEN}==================== 0点抢话费脚本 v1.6 ===================={Color.ENDC}
'''

def printn(m):
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f'\n[{Color.OKCYAN}{current_time}{Color.ENDC}] {m}')

def print_info(m):
    print(f'[{Color.OKGREEN}INFO{Color.ENDC}] {m}')

def print_warn(m):
    print(f'[{Color.WARNING}WARN{Color.ENDC}] {m}')

def print_error(m):
    print(f'[{Color.FAIL}ERROR{Color.ENDC}] {m}')

def print_success(m):
    print(f'[{Color.OKGREEN}SUCCESS{Color.ENDC}] {m}')

context = ssl.create_default_context()
context.set_ciphers('DEFAULT@SECLEVEL=1')  # 低安全级别0/1
context.check_hostname = False  # 禁用主机
context.verify_mode = ssl.CERT_NONE  # 禁用证书

class DESAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

import urllib3
urllib3.disable_warnings()
ss = requests.session()
ss.headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
    "Referer": "https://wapact.189.cn:9001/JinDouMall/JinDouMall_independentDetails.html"
}
ss.mount('https://', DESAdapter())

# 修复：使用正确的方式禁用cookie
class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False

# 使用自定义的CookiePolicy
ss.cookies.set_policy(BlockAll())

run_num = os.environ.get('reqNUM') or "5"

MAX_RETRIES = 3
RATE_LIMIT = 10  # 每秒请求数限制

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.updated_at = time.monotonic()

    async def acquire(self):
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.rate_limit
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.rate_limit)
            self.updated_at = now

class AsyncSessionManager:
    def __init__(self):
        self.session = None
        self.connector = None

    async def __aenter__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
        self.connector = TCPConnector(ssl=ssl_context, limit=1000)
        self.session = ClientSession(connector=self.connector)
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()

async def retry_request(session, method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            await asyncio.sleep(1)
            async with session.request(method, url,** kwargs) as response:
                return await response.json()
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
            print_error(f"请求失败，第 {attempt + 1} 次重试: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(2 **attempt)

key = b'1234567`90koiuyhgtfrdews'
iv = 8 * b'\0'

public_key_b64 = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBkLT15ThVgz6/NOl6s8GNPofdWzWbCkWnkaAm7O2LjkM1H7dMvzkiqdxU02jamGRHLX/ZNMCXHnPcW/sDhiFCBN18qFvy8g6VYb9QtroI09e176s+ZCtiv7hbin2cCTj99iUpnEloZm19lwHyo69u5UMiPMpq0/XKBO8lYhN/gwIDAQAB
-----END PUBLIC KEY-----'''

public_key_data = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+ugG5A8cZ3FqUKDwM57GM4io6JGcStivT8UdGt67PEOihLZTw3P7371+N47PrmsCpnTRzbTgcupKtUv8ImZalYk65dU8rjC/ridwhw9ffW2LBwvkEnDkkKKRi2liWIItDftJVBiWOh17o6gfbPoNrWORcAdcbpk2L+udld5kZNwIDAQAB
-----END PUBLIC KEY-----'''

def get_first_three(value):
    if isinstance(value, (int, float)):
        return int(str(value)[:3])
    elif isinstance(value, str):
        return str(value)[:3]
    else:
        raise TypeError("error")

def run_Time(hour, minute, second):
    date = datetime.datetime.now()
    date_zero = datetime.datetime.now().replace(year=date.year, month=date.month, day=date.day, hour=hour, minute=minute, second=second)
    date_zero_time = int(time.mktime(date_zero.timetuple()))
    return date_zero_time

def encrypt(text):
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(text.encode(), DES3.block_size))
    return ciphertext.hex()

def decrypt(text):
    ciphertext = bytes.fromhex(text)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), DES3.block_size)
    return plaintext.decode()

def b64(plaintext):
    public_key = RSA.import_key(public_key_b64)
    cipher = PKCS1_v1_5.new(public_key)
    ciphertext = cipher.encrypt(plaintext.encode())
    return base64.b64encode(ciphertext).decode()

def encrypt_para(plaintext):
    if not isinstance(plaintext, str):
        plaintext = json.dumps(plaintext)
    public_key = RSA.import_key(public_key_data)
    cipher = PKCS1_v1_5.new(public_key)
    ciphertext = cipher.encrypt(plaintext.encode())
    return binascii.hexlify(ciphertext).decode()

def encrypt_paraNew(p):
    k = RSA.import_key(public_key_data)
    c = PKCS1_v1_5.new(k)
    s = k.size_in_bytes() - 11
    d = p.encode() if isinstance(p, str) else json.dumps(p).encode()
    return binascii.hexlify(b''.join(c.encrypt(d[i:i+s]) for i in range(0, len(d), s))).decode()

def encode_phone(text):
    encoded_chars = []
    for char in text:
        encoded_chars.append(chr(ord(char) + 2))
    return ''.join(encoded_chars)

def userLoginNormal(phone, password):
    alphabet = 'abcdef0123456789'
    uuid = [''.join(random.sample(alphabet, 8)), ''.join(random.sample(alphabet, 4)),
            '4' + ''.join(random.sample(alphabet, 3)), ''.join(random.sample(alphabet, 4)),
            ''.join(random.sample(alphabet, 12))]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    loginAuthCipherAsymmertric = 'iPhone 14 15.4.' + uuid[0] + uuid[1] + phone + timestamp + password[:6] + '0$$$0.'
    
    try:
        r = ss.post(
            'https://appgologin.189.cn:9031/login/client/userLoginNormal',
            json={
                "headerInfos": {
                    "code": "userLoginNormal",
                    "timestamp": timestamp,
                    "broadAccount": "",
                    "broadToken": "",
                    "clientType": "#11.3.0#channel35#Xiaomi Redmi K30 Pro#",
                    "shopId": "20002",
                    "source": "110003",
                    "sourcePassword": "Sid98s",
                    "token": "",
                    "userLoginName": encode_phone(phone)
                },
                "content": {
                    "attach": "test",
                    "fieldData": {
                        "loginType": "4",
                        "accountType": "",
                        "loginAuthCipherAsymmertric": b64(loginAuthCipherAsymmertric),
                        "deviceUid": uuid[0] + uuid[1] + uuid[2],
                        "phoneNum": encode_phone(phone),
                        "isChinatelecom": "0",
                        "systemVersion": "12",
                        "authentication": encode_phone(password)
                    }
                }
            },
            verify=certifi.where()
        ).json()
        
        l = r['responseData']['data']['loginSuccessResult']
        if l:
            ticket = get_ticket(phone, l['userId'], l['token'])
            return ticket
        return False
    except Exception as e:
        print_error(f"登录请求异常: {str(e)}")
        return False

async def exchangeForDay(phone, session, run_num, rid, stime, accId):
    async def delayed_conversion(delay):
        await asyncio.sleep(delay)
        await conversionRights(phone, rid, session, accId)
    tasks = [asyncio.create_task(delayed_conversion(i * stime)) for i in range(int(run_num))]
    await asyncio.gather(*tasks)

def get_ticket(phone, userId, token):
    try:
        r = ss.post(
            'https://appgologin.189.cn:9031/map/clientXML',
            data='<Request><HeaderInfos><Code>getSingle</Code><Timestamp>'+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+'</Timestamp><BroadAccount></BroadAccount><BroadToken></BroadToken><ClientType>#9.6.1#channel50#iPhone 14 Pro Max#</ClientType><ShopId>20002</ShopId><Source>110003</Source><SourcePassword>Sid98s</SourcePassword><Token>'+token+'</Token><UserLoginName>'+phone+'</UserLoginName></HeaderInfos><Content><Attach>test</Attach><FieldData><TargetId>'+encrypt(userId)+'</TargetId><Url>4a6862274835b451</Url></FieldData></Content></Request>',
            headers={'user-agent': 'CtClient;10.4.1;Android;13;22081212C;NTQzNzgx!#!MTgwNTg1'},
            verify=certifi.where()
        )
        tk = re.findall('<Ticket>(.*?)</Ticket>', r.text)
        if len(tk) == 0:
            return False
        return decrypt(tk[0])
    except Exception as e:
        print_error(f"获取ticket异常: {str(e)}")
        return False

async def exchange(s, phone, title, rid, jsexec, ckvalue):
    try:
        url = "https://wapact.189.cn:9001/gateway/standExchange/detailNew/exchange"
        get_url = await asyncio.to_thread(jsexec.call, "getUrl", "POST", url)
        async with s.post(get_url, cookies=ckvalue, json={"activityId": rid}) as response:
            pass
    except Exception as e:
        print_error(e)

async def check(s, item, ckvalue):
    checkGoods = s.get('https://wapact.189.cn:9001/gateway/stand/detailNew/check?activityId=' + item, cookies=ckvalue).json()
    return checkGoods

async def conversionRights(phone, rid, session, accId):
    try:
        ruishu_cookies = get_ruishu_cookies()
        if not ruishu_cookies:
            print_warn(f"{get_first_three(phone)}: 无法获取 Ruishu cookies")
            return

        value = {
            "id": rid,
            "accId": accId,
            "showType": "9003",
            "showEffect": "8",
            "czValue": "0"
        }
        paraV = encrypt_paraNew(value)

        printn(f"{Color.OKGREEN}{get_first_three(phone)}: 开始兑换{Color.ENDC}")

        response = session.post(
            'https://wappark.189.cn/jt-sign/paradise/receiverRights',
            json={"para": paraV},
            cookies=ruishu_cookies
        )

        login = response.json()
        printn(f"{get_first_three(phone)}: {login}")

        if '兑换成功' in response.text:
            print_success(f"{get_first_three(phone)}: 兑换成功!")
            # QLAPI.notify(get_first_three(phone), login['resoultMsg'])
            #exit(0)

    except Exception as e:
        print_error(f"{get_first_three(phone)}: 兑换请求发生错误: {str(e)}")

async def getLevelRightsList(phone, session, accId):
    try:
        ruishu_cookies = get_ruishu_cookies()
        if not ruishu_cookies:
            print_warn("无法获取 Ruishu cookies")
            return None

        value = {
            "type": "hg_qd_djqydh",
            "accId": accId,
            "shopId": "20001"
        }
        paraV = encrypt_paraNew(value)

        response = session.post(
            'https://wappark.189.cn/jt-sign/paradise/queryLevelRightInfo',
            json={"para": paraV},
            cookies=ruishu_cookies
        )

        data = response.json()
        if data.get('code') == 401:
            print_warn(f"获取失败:{data}, 原因大概是sign过期了")
            return None

        current_level = int(data['currentLevel'])
        key_name = 'V' + str(current_level)
        ids = [item['activityId'] for item in data.get(key_name, []) if '话费' in item.get('title', "")]
        return ids

    except Exception as e:
        print_warn(f"获取失败, 重试一次: {str(e)}")
        try:
            ruishu_cookies = get_ruishu_cookies()
            if not ruishu_cookies:
                print_warn("重试时无法获取 Ruishu cookies")
                return None

            paraV = encrypt_para(value)
            response = session.post(
                'https://wappark.189.cn/jt-sign/paradise/getLevelRightsList',
                json={"para": paraV},
                cookies=ruishu_cookies
            )

            data = response.json()
            if data.get('code') == 401:
                print_warn(f"重试获取失败:{data}, 原因大概是sign过期了")
                return None

            current_level = int(data['currentLevel'])
            key_name = 'V' + str(current_level)
            ids = [item['activityId'] for item in data.get(key_name, []) if '话费' in item.get('title', "")]
            return ids

        except Exception as e:
            print_error(f"重试也失败了: {str(e)}")
            return None

def get_ruishu_cookies():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ruishu_path = os.path.join(current_dir, 'Ruishu.py')

        result = subprocess.run(
            [sys.executable, ruishu_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print_error(f"Ruishu.py 执行错误: {result.stderr}")
            return None

        cookies = json.loads(result.stdout.strip())
        return cookies

    except Exception as e:
        print_error(f"获取 Ruishu cookies 时发生错误: {str(e)}")
        return None

async def getSign(ticket, session):
    try:
        ruishu_cookies = get_ruishu_cookies()
        if not ruishu_cookies:
            print_warn("无法获取 Ruishu cookies")
            return None

        cookies = {**ruishu_cookies}

        response = session.get(
            'https://wappark.189.cn/jt-sign/ssoHomLogin?ticket=' + ticket,
            cookies=cookies,
            headers={
                'User-Agent': "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36"
            }
        ).json()

        if response.get('resoultCode') == '0':
            sign = response.get('sign')
            accId = response.get('accId')
            return sign, accId
        else:
            print_warn(f"获取sign失败[{response.get('resoultCode')}]: {response}")
    except Exception as e:
        print_error(f"getSign 发生错误: {str(e)}")
    return None

async def qgNight(phone, ticket, timeDiff, isTrue):
    if isTrue:
        runTime = run_Time(23, 59, 3)
    else:
        runTime = 0

    if runTime > (time.time() + timeDiff):
        difftime = runTime - time.time() - timeDiff
        printn(f"当前时间:{str(datetime.datetime.now())[11:23]}, 跟设定的时间不同, 等待{difftime}秒开始兑换每天一次的")
        await asyncio.sleep(difftime)
    
    session = requests.Session()
    session.mount('https://', DESAdapter())
    session.verify = False  # 禁用证书验证
    signx = await getSign(ticket, session)
    
    if signx:
        sign, accId = signx
        printn(f"当前时间:{str(datetime.datetime.now())[11:23]}获取到了Sign: {Color.OKGREEN}{sign}{Color.ENDC}")
        session.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
            "sign": sign
        }
    else:
        print_warn("未获取sign。")
        return

    rightsId = await getLevelRightsList(phone, session, accId)
    if rightsId:
        printn(f"获取到了rightsId: {Color.OKGREEN}{rightsId[0]}{Color.ENDC}")
    else:
        print_warn("未能获取rightsId。")
        return

    if isTrue:
        runTime2 = run_Time(23, 59, 56) + 0.3
        difftime = runTime2 - time.time() - timeDiff
        printn(f"等待{difftime}s")
        await asyncio.sleep(difftime)
    
    await exchangeForDay(phone, session, run_num, rightsId[0], 0.1, accId)

async def qgDay(phone, ticket, timeDiff, isTrue):
    async with AsyncSessionManager() as s:
        pass

async def main(timeDiff, isTRUE, hour):
    print(LOGO)
    print_info("脚本初始化完成，开始准备抢话费...")

    
    tasks = []
    PHONES = os.environ.get('chinaTelecomAccount')
    
    if not PHONES:
        print_error("错误: 未设置 chinaTelecomAccount 环境变量，请配置为 账号#密码 格式")
        return
    
    # 支持多种分隔符：& 和换行符
    phone_list = []
    for separator in ['&', '\n', '\r\n']:
        if separator in PHONES:
            phone_list = PHONES.split(separator)
            break
    else:
        # 如果没有找到分隔符，就当作单个账号处理
        phone_list = [PHONES]
    
    # 过滤空字符串
    phone_list = [phone.strip() for phone in phone_list if phone.strip()]
    
    print_info(f"检测到 {len(phone_list)} 个账号将参与抢话费")
    
    for phoneV in phone_list:
        value = phoneV.split('#')
        if len(value) != 2:
            print_warn(f"跳过无效账号格式: {phoneV}，请使用 账号#密码 格式")
            continue
            
        phone, password = value[0], value[1]
        printn(f"{Color.OKBLUE}{get_first_three(phone)}: 开始登录{Color.ENDC}")
        
        max_retries = 3
        retry_count = 0
        ticket = None
        
        while retry_count < max_retries and not ticket:
            ticket = userLoginNormal(phone, password)
            if not ticket:
                print_warn(f"{get_first_three(phone)}: 第{retry_count+1}次登录失败，准备重试")
                retry_count += 1
                await asyncio.sleep(1)  # 添加1秒延迟避免频繁请求

        if ticket:
            print_success(f"{get_first_three(phone)}: 登录成功")
            if hour > 15:
                tasks.append(qgNight(phone, ticket, timeDiff, isTRUE))
            else:  # 十点//十四点场次
                tasks.append(qgNight(phone, ticket, timeDiff, isTRUE))
        else:
            print_error(f"{get_first_three(phone)}: 登录失败，已达最大重试次数{max_retries}次")
    
    if tasks:
        print_info(f"准备执行 {len(tasks)} 个抢话费任务")
        await asyncio.gather(*tasks)
    else:
        print_warn("没有可执行的抢话费任务")

if __name__ == "__main__":
    test0 = os.getenv('test0')
    print_info("脚本启动中...")
    print_info(f"环境变量配置: chinaTelecomAccount = {os.environ.get('chinaTelecomAccount', '未设置')}")
    print_info(f"请求次数配置: reqNUM = {run_num}")
    print_info(f"测试模式配置: test0 = {test0} (1为正常模式，0为测试模式，默认为1)")
    h = datetime.datetime.now().hour
    print_info(f"当前系统时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 10 > h > 0:
        print_info(f"当前小时为: {h} 已过0点但未到10点，v开始准备抢凌晨场次")
        wttime = run_Time(23, 59, 8)  # 抢十点场次
    elif 14 >= h >= 10:
        print_info(f"当前小时为: {h} 已过10点但未到14点，开始准备抢凌晨场次")
        wttime = run_Time(23, 59, 8)  # 抢十四点场次
    else:
        print_info(f"当前小时为: {h} 已过14点，开始准备抢凌晨场次")
        wttime = run_Time(23, 58, 58)  # 抢凌晨场次
    
    
    isTRUE = os.getenv('test0', '1') not in ['0', 'false', 'False'] #实际生产环境设为True，测试时可设为False忽略时间限制
    
    if wttime > time.time():
        wTime = wttime - time.time()
        print_info(f"未到抢话费时间，计算后等待: {wTime:.2f} 秒")
        if isTRUE:
            print_warn("注意: 一定要先测试，根据自身网络设定重发次数和多账号策略，避免抢购过早或过晚")
            print_info("开始等待抢话费时间...")
            time.sleep(wTime)
    
    timeValue = 0  # getApiTime("https://f.m.suning.com/api/ct.do")
    timeDiff = timeValue if timeValue > 0 else 0
    try:
        asyncio.run(main(timeDiff, isTRUE, h))
    except Exception as e:
        print_error(f"脚本执行过程中发生异常: {str(e)}")
    finally:
        print_info("所有任务都已执行完毕!")
