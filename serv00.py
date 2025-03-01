/*
    name: "serv00保活"
    cron: 0 0,8 * * *
    更新时间:2025-03-01
    # 环境变量中设置SSH_INFO = host1 username1 password1@host2 username2 password2
    # 支持多账号,用@分隔
*/
import os
import subprocess


# 获取环境变量中的 SSH 信息
ssh_info = os.getenv("SSH_INFO")

# 检查环境变量是否存在
if not ssh_info:
    raise ValueError("SSH 信息未在环境变量中设置")

# 将 SSH 信息按 @ 分割成多个账号
accounts = ssh_info.split('@')

# 遍历每个账号
for account in accounts:
    # 将每个账号的信息按空格分割
    try:
        ssh_host, ssh_user, ssh_password = account.split()
    except ValueError:
        print(f"账号格式不正确: {account}")
        continue

    # 构建 ssh 命令，跳过主机密钥验证并使用密码认证
    ssh_command = f"sshpass -p '{ssh_password}' ssh -o StrictHostKeyChecking=no {ssh_user}@{ssh_host} hostname"

    # 使用 subprocess 执行 SSH 命令
    try:
        print(f"尝试连接 {ssh_host}...")
        # 执行命令并捕获输出
        result = subprocess.run(ssh_command, shell=True, text=True, capture_output=True, check=True)
        
        # 获取并打印命令输出
        print(f"Command Output: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.stderr}")
    except Exception as e:
        print(f"连接 SSH 时发生错误: {e}")
