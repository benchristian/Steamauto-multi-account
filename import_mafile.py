#!/usr/bin/env python3
"""
根据实例目录名 {steam_username}_{steam_id} 自动配置 steam_account_info.json5

原理：
  目录名格式: gunzaleztravers234_76561198750624814
  从目录名解析出 steam_username 和 steam_id，
  再从 steam-desktop-authenticator 的 maFile 中读取 shared_secret / identity_secret，
  最终写入 config/steam_account_info.json5。

用法:
  python3 import_mafile.py [--accounts-dir <path>] [--mafiles-dir <path>]

作者: CodeBuddy AI
"""

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


def log_info(msg):
    print(f"{CYAN}[INFO]{NC} {msg}")


def log_ok(msg):
    print(f"{GREEN}[OK]{NC} {msg}")


def log_warn(msg):
    print(f"{YELLOW}[WARN]{NC} {msg}")


def log_err(msg):
    print(f"{RED}[ERR]{NC} {msg}")


def scan_mafiles(mafiles_dir):
    """扫描 maFiles 目录，返回 {steam_id: {account_name, shared_secret, identity_secret}}"""
    if not os.path.isdir(mafiles_dir):
        log_err(f"MaFiles 目录不存在: {mafiles_dir}")
        sys.exit(1)

    files = glob.glob(os.path.join(mafiles_dir, "*.maFile"))
    if not files:
        log_err(f"MaFiles 目录下没有找到 .maFile 文件: {mafiles_dir}")
        sys.exit(1)

    result = {}
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            log_warn(f"无法解析 {os.path.basename(f)}: {e}")
            continue

        steam_id = str(data.get('SteamID', '')).strip()
        account_name = data.get('account_name', '').strip()

        if not steam_id or not account_name:
            continue

        result[steam_id] = {
            'steam_id': steam_id,
            'account_name': account_name,
            'shared_secret': data.get('shared_secret', '').strip(),
            'identity_secret': data.get('identity_secret', '').strip(),
        }

    return result


def parse_instance_name(name):
    """
    解析实例目录名 {steam_username}_{steam_id}
    steam_id 特征: 纯数字，开头为 765611，长度 17 位
    返回 (steam_username, steam_id) 或 (None, None)
    """
    # steam_id 固定以 765611 开头且为 17 位数字（765611 + 11位）
    m = re.match(r'^(.+?)_(765611\d{11})$', name)
    if m:
        return m.group(1), m.group(2)
    return None, None


def find_instances(accounts_dir):
    """遍历 accounts 目录，返回所有实例信息"""
    if not os.path.isdir(accounts_dir):
        log_err(f"Accounts 目录不存在: {accounts_dir}")
        sys.exit(1)

    instances = []
    for buff_dir in os.listdir(accounts_dir):
        buff_path = os.path.join(accounts_dir, buff_dir)
        if not os.path.isdir(buff_path):
            continue
        if buff_dir.startswith('.'):
            continue

        for inst_name in os.listdir(buff_path):
            inst_path = os.path.join(buff_path, inst_name)
            if not os.path.isdir(inst_path):
                continue
            if inst_name.startswith('.'):
                continue

            config_dir = os.path.join(inst_path, 'config')
            info_file = os.path.join(config_dir, 'steam_account_info.json5')

            instances.append({
                'buff': buff_dir,
                'name': inst_name,
                'path': inst_path,
                'info_file': info_file if os.path.isdir(config_dir) else None,
                'config_dir': config_dir if os.path.isdir(config_dir) else None,
            })

    return instances


def write_steam_account_info(info_file, account_name, shared_secret, identity_secret):
    """写入 steam_account_info.json5"""
    content = f"""{{
  // Steam 令牌参数（用于身份验证）
  "shared_secret": "{shared_secret}",

  // Steam 令牌参数（用于身份验证）
  "identity_secret": "{identity_secret}",

  // Steam 登录时填写的用户名
  "steam_username": "{account_name}",

  // Steam 登录时填写的密码
  "steam_password": ""
}}
"""
    os.makedirs(os.path.dirname(info_file), exist_ok=True)
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='根据目录名 {username}_{steam_id} 自动配置 steam_account_info.json5')
    parser.add_argument('--accounts-dir', default=None,
                        help='accounts 目录路径，默认为 ./accounts')
    parser.add_argument('--mafiles-dir', default=None,
                        help='MaFiles 目录路径，默认为 ~/Library/Application Support/steam-desktop-authenticator/maFiles')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅显示匹配结果，不实际写入')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    accounts_dir = args.accounts_dir or os.path.join(script_dir, 'accounts')
    mafiles_dir = args.mafiles_dir or os.path.join(
        os.path.expanduser('~'),
        'Library/Application Support/steam-desktop-authenticator/maFiles'
    )

    print(f"{CYAN}============================================{NC}")
    print(f"  MaFile 自动配置工具")
    print(f"{CYAN}============================================{NC}")
    print(f"  MaFiles 目录: {mafiles_dir}")
    print(f"  Accounts 目录: {accounts_dir}")
    print()

    log_info("扫描 MaFiles...")
    mafiles = scan_mafiles(mafiles_dir)
    log_info(f"共 {len(mafiles)} 个有效 maFile")

    log_info("扫描实例目录...")
    instances = find_instances(accounts_dir)
    log_info(f"共 {len(instances)} 个实例目录")

    matched = 0
    skipped_parsed = 0
    skipped_no_mafile = 0
    skipped_no_config = 0
    skipped_already = 0

    for inst in instances:
        buff = inst['buff']
        name = inst['name']
        label = f"{buff}/{name}"

        # 1. 解析目录名
        steam_username, steam_id = parse_instance_name(name)
        if not steam_id:
            log_warn(f"{label}: 目录名无法解析为 steam_username_steam_id 格式，跳过")
            skipped_parsed += 1
            continue

        # 2. 查找对应 maFile
        if steam_id not in mafiles:
            log_warn(f"{label}: 未找到 SteamID={steam_id} 的 maFile，跳过")
            skipped_no_mafile += 1
            continue

        mafile = mafiles[steam_id]

        # 3. 检查是否已有配置
        info_file = inst['info_file']
        if info_file and os.path.isfile(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                text_clean = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
                text_clean = re.sub(r'/\*.*?\*/', '', text_clean, flags=re.DOTALL)
                cfg = json.loads(text_clean)
                existing_secret = cfg.get('shared_secret', '').strip()
                if existing_secret:
                    log_warn(f"{label}: 已有 shared_secret，跳过")
                    skipped_already += 1
                    continue
            except Exception:
                pass

        if not inst['config_dir']:
            log_warn(f"{label}: 没有 config 目录，跳过")
            skipped_no_config += 1
            continue

        # 4. 写入配置
        if args.dry_run:
            print(f"  {YELLOW}[DRY]{NC} {steam_username} (SteamID: {steam_id}) -> {label}")
        else:
            write_steam_account_info(
                info_file,
                account_name=mafile['account_name'],
                shared_secret=mafile['shared_secret'],
                identity_secret=mafile['identity_secret'],
            )
            print(f"  {GREEN}OK{NC} {steam_username} (SteamID: {steam_id}) -> {label}")
        matched += 1

    print()
    total = matched + skipped_parsed + skipped_no_mafile + skipped_no_config + skipped_already
    if args.dry_run:
        log_info(f"Dry Run 完成: 将配置 {matched} 个，跳过 {total - matched} 个")
    else:
        log_ok(f"完成: 成功配置 {matched} 个，跳过 {total - matched} 个")

    if skipped_parsed > 0:
        log_warn(f"  - {skipped_parsed} 个目录名不符合 {{username}}_{{steam_id}} 格式")
    if skipped_no_mafile > 0:
        log_warn(f"  - {skipped_no_mafile} 个 SteamID 未找到对应 maFile")
    if skipped_already > 0:
        log_warn(f"  - {skipped_already} 个已有 shared_secret，跳过")


if __name__ == '__main__':
    main()
