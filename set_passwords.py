#!/usr/bin/env python3
"""从 CSV 文件批量写入 steam_password 到 steam_account_info.json5"""

import csv
import json
import os
import re
import sys

GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

accounts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'accounts')
csv_path = sys.argv[1] if len(sys.argv) > 1 else '/Users/lucidity/CodeBuddy/steam账号.csv'

# 读取 CSV
passwords = {}
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) >= 2:
            username = row[0].strip()
            pwd = row[1].strip()
            if username and pwd:
                passwords[username.lower()] = pwd

print(f"从 CSV 读取到 {len(passwords)} 条账号密码")

# 遍历所有实例
success = 0
skipped_no_user = 0
skipped_no_match = 0
skipped_has_pwd = 0

for buff_dir in os.listdir(accounts_dir):
    buff_path = os.path.join(accounts_dir, buff_dir)
    if not os.path.isdir(buff_path) or buff_dir.startswith('.'):
        continue

    for inst_name in os.listdir(buff_path):
        inst_path = os.path.join(buff_path, inst_name)
        if not os.path.isdir(inst_path) or inst_name.startswith('.'):
            continue

        info_file = os.path.join(inst_path, 'config', 'steam_account_info.json5')
        if not os.path.isfile(info_file):
            continue

        label = f"{buff_dir}/{inst_name}"

        # 读取当前 steam_username
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                text = f.read()
            text_clean = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
            text_clean = re.sub(r'/\*.*?\*/', '', text_clean, flags=re.DOTALL)
            cfg = json.loads(text_clean)
        except Exception:
            continue

        steam_username = cfg.get('steam_username', '').strip()

        if not steam_username:
            print(f"{YELLOW}SKIP{NC} {label}: steam_username 为空")
            skipped_no_user += 1
            continue

        # 已有密码则跳过
        if cfg.get('steam_password', '').strip():
            print(f"{YELLOW}SKIP{NC} {label}: 已有密码")
            skipped_has_pwd += 1
            continue

        # 大小写不敏感匹配
        pwd = passwords.get(steam_username.lower())
        if not pwd:
            print(f"{RED}MISS{NC} {label}: steam_username={steam_username} 未在 CSV 中找到")
            skipped_no_match += 1
            continue

        # 写入密码
        new_text = re.sub(
            r'"steam_password":\s*""',
            f'"steam_password": "{pwd}"',
            text
        )
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(new_text)

        print(f"{GREEN}OK{NC} {label}: {steam_username}")
        success += 1

print()
print(f"完成: 成功 {success}, 跳过 {skipped_no_user + skipped_no_match + skipped_has_pwd}")
print(f"  - 用户名为空: {skipped_no_user}")
print(f"  - CSV 中未匹配: {skipped_no_match}")
print(f"  - 已有密码: {skipped_has_pwd}")
