#!/usr/bin/env python3
"""
批量写入完整的 steam_account_info.json5

数据来源:
  - steam账号.csv: steam_username, steam_password
  - maFile 目录: shared_secret, identity_secret

用法:
  python3 write_account_info.py [--csv <csv文件>] [--mafiles-dir <maFile目录>] [--dry-run]

作者: CodeBuddy AI
"""

import csv
import glob
import json
import os
import re
import sys

GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_csv_passwords(csv_path):
    """读取 CSV，返回 {steam_username_lower: password}"""
    if not os.path.isfile(csv_path):
        print(f"{RED}[ERR]{NC} CSV 文件不存在: {csv_path}")
        sys.exit(1)

    passwords = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 2:
                username = row[0].strip()
                pwd = row[1].strip()
                if username and pwd:
                    passwords[username.lower()] = pwd
    return passwords


def load_mafiles(mafiles_dir):
    """扫描 maFiles 目录，返回 {steam_id: {shared_secret, identity_secret, account_name}}"""
    if not os.path.isdir(mafiles_dir):
        print(f"{RED}[ERR]{NC} MaFiles 目录不存在: {mafiles_dir}")
        sys.exit(1)

    files = glob.glob(os.path.join(mafiles_dir, "*.maFile"))
    if not files:
        print(f"{RED}[ERR]{NC} 未找到 .maFile 文件: {mafiles_dir}")
        sys.exit(1)

    result = {}
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            print(f"{YELLOW}[WARN]{NC} 无法解析 {os.path.basename(f)}: {e}")
            continue

        steam_id = str(data.get('SteamID', '')).strip()
        account_name = data.get('account_name', '').strip()
        if not steam_id:
            continue

        result[steam_id] = {
            'account_name': account_name.lower(),
            'shared_secret': data.get('shared_secret', '').strip(),
            'identity_secret': data.get('identity_secret', '').strip(),
        }

    return result


def write_info_file(info_file, steam_username, steam_password, shared_secret, identity_secret):
    """写入完整的 steam_account_info.json5"""
    content = f"""{{
  // Steam 令牌参数（用于身份验证）
  "shared_secret": "{shared_secret}",

  // Steam 令牌参数（用于身份验证）
  "identity_secret": "{identity_secret}",

  // Steam 登录时填写的用户名
  "steam_username": "{steam_username}",

  // Steam 登录时填写的密码
  "steam_password": "{steam_password}"
}}
"""
    os.makedirs(os.path.dirname(info_file), exist_ok=True)
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(content)


def parse_instance_name(name):
    """解析 {steam_username}_{steam_id}，返回 (username, steam_id)"""
    m = re.match(r'^(.+?)_(765611\d{11})$', name)
    if m:
        return m.group(1), m.group(2)
    return None, None


def find_instances(accounts_dir):
    """遍历所有实例"""
    instances = []
    for buff_dir in sorted(os.listdir(accounts_dir)):
        buff_path = os.path.join(accounts_dir, buff_dir)
        if not os.path.isdir(buff_path) or buff_dir.startswith('.'):
            continue
        for inst_name in sorted(os.listdir(buff_path)):
            inst_path = os.path.join(buff_path, inst_name)
            if not os.path.isdir(inst_path) or inst_name.startswith('.'):
                continue
            config_dir = os.path.join(inst_path, 'config')
            info_file = os.path.join(config_dir, 'steam_account_info.json5')
            instances.append({
                'buff': buff_dir,
                'name': inst_name,
                'path': inst_path,
                'info_file': info_file,
            })
    return instances


def main():
    import argparse
    parser = argparse.ArgumentParser(description='批量写入 steam_account_info.json5')
    parser.add_argument('--csv', default=os.path.join(SCRIPT_DIR, 'steam账号.csv'),
                        help='CSV 文件路径 (默认: ./steam账号.csv)')
    parser.add_argument('--mafiles-dir', default=os.path.join(
        os.path.expanduser('~'),
        'Library/Application Support/steam-desktop-authenticator/maFiles'),
        help='maFiles 目录路径')
    parser.add_argument('--accounts-dir', default=os.path.join(SCRIPT_DIR, 'accounts'),
                        help='accounts 目录路径')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅预览，不实际写入')
    args = parser.parse_args()

    print(f"{CYAN}============================================{NC}")
    print(f"  批量写入 steam_account_info.json5")
    print(f"{CYAN}============================================{NC}")
    print(f"  CSV:        {args.csv}")
    print(f"  MaFiles:    {args.mafiles_dir}")
    print(f"  Accounts:   {args.accounts_dir}")
    print()

    # 加载数据
    print(f"{CYAN}[1/3]{NC} 读取 CSV 密码...")
    passwords = load_csv_passwords(args.csv)
    print(f"     共 {len(passwords)} 条密码")

    print(f"{CYAN}[2/3]{NC} 扫描 MaFiles...")
    mafiles = load_mafiles(args.mafiles_dir)
    print(f"     共 {len(mafiles)} 个有效 maFile")

    print(f"{CYAN}[3/3]{NC} 扫描实例...")
    instances = find_instances(args.accounts_dir)
    print(f"     共 {len(instances)} 个实例")
    print()

    # 匹配并写入
    stats = {'ok': 0, 'no_steam_id': 0, 'no_mafile': 0, 'no_password': 0, 'skip': 0}

    for inst in instances:
        label = f"{inst['buff']}/{inst['name']}"

        # 解析 steam_id
        steam_username, steam_id = parse_instance_name(inst['name'])
        if not steam_id:
            print(f"{YELLOW}[SKIP]{NC} {label} — 目录名无法解析")
            stats['no_steam_id'] += 1
            continue

        # 查找 maFile
        if steam_id not in mafiles:
            print(f"{YELLOW}[SKIP]{NC} {label} — SteamID {steam_id} 无对应 maFile")
            stats['no_mafile'] += 1
            continue

        mafile = mafiles[steam_id]
        shared_secret = mafile['shared_secret']
        identity_secret = mafile['identity_secret']

        # 查找密码（大小写不敏感）
        password = passwords.get(steam_username.lower())
        if not password:
            print(f"{RED}[MISS]{NC} {label} — {steam_username} 在 CSV 中无密码")
            stats['no_password'] += 1
            continue

        # 写入
        if args.dry_run:
            print(f"{CYAN}[DRY]{NC}  {label}")
            print(f"        username={steam_username}, steam_id={steam_id}")
            print(f"        shared_secret={'有' if shared_secret else '无'}, "
                  f"identity_secret={'有' if identity_secret else '无'}, "
                  f"password={'有' if password else '无'}")
        else:
            write_info_file(inst['info_file'], steam_username, password, shared_secret, identity_secret)
            print(f"{GREEN}[OK]{NC}  {label} — {steam_username}")
        stats['ok'] += 1

    # 汇总
    print()
    print(f"{CYAN}============================================{NC}")
    total = sum(stats.values())
    print(f"  总计: {total} 个实例")
    print(f"  {GREEN}成功: {stats['ok']}{NC}")
    print(f"  {YELLOW}跳过 (无steam_id): {stats['no_steam_id']}{NC}")
    print(f"  {YELLOW}跳过 (无maFile): {stats['no_mafile']}{NC}")
    print(f"  {RED}跳过 (无密码): {stats['no_password']}{NC}")
    print(f"{CYAN}============================================{NC}")


if __name__ == '__main__':
    main()
