#!/usr/bin/env python3
"""
Steamauto 出售统计脚本
用法:
  python3 stats.py <实例路径>              # 统计单个实例
  python3 stats.py --all                   # 统计所有实例
  python3 stats.py --buff <BUFF号>         # 统计某BUFF号下所有实例
  python3 stats.py --list                  # 列出所有实例及其统计文件

数据来源优先级:
  1. BUFF API 出售历史（/api/market/sell_order/history）
  2. 本地日志文件解析

输出文件: <实例目录>/<steam_username>_<steam_id>.txt
格式参考: 每笔订单包含 订单ID/平台订单号/订单状态/时间/平台/商品名称/磨损值/商品ID/售价/手续费/净收入
"""

import json
import os
import re
import sys
import time
import requests
import glob
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 确保 Steamauto 模块可导入
STEAMAUTO_DIR = os.path.join(SCRIPT_DIR, "Steamauto")
if STEAMAUTO_DIR not in sys.path:
    sys.path.insert(0, STEAMAUTO_DIR)

from utils.static import CURRENT_VERSION

# ============================================================
# 配置
# ============================================================

def get_ua():
    import random
    first_num = random.randint(55, 62)
    third_num = random.randint(0, 3200)
    fourth_num = random.randint(0, 140)
    os_type = [
        "(Windows NT 6.1; WOW64)",
        "(Windows NT 10.0; WOW64)",
        "(X11; Linux x86_64)",
        "(Macintosh; Intel Mac OS X 10_12_6)",
    ]
    chrome_version = f"Chrome/{first_num}.0.{third_num}.{fourth_num}"
    return " ".join([
        "Mozilla/5.0",
        random.choice(os_type),
        "AppleWebKit/537.36",
        "(KHTML, like Gecko)",
        chrome_version,
        "Safari/537.36",
    ])


BUFF_BASE_URL = "https://buff.163.com"
PROGRAM_VERSION = CURRENT_VERSION


# ============================================================
# 读取配置
# ============================================================

def read_json5_config(filepath):
    """简易 JSON5 解析（支持 // 注释和尾部逗号）"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    # 去掉单行注释
    text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    # 去掉块注释
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return json.loads(text)


def get_steam_info(instance_dir):
    """从 steam_account_info.json5 读取 Steam 账号信息"""
    info_path = os.path.join(instance_dir, "config", "steam_account_info.json5")
    if os.path.exists(info_path):
        try:
            return read_json5_config(info_path)
        except Exception:
            pass
    return {}


def get_buff_cookie(instance_dir):
    """从 config 目录读取 BUFF cookie"""
    config_dir = os.path.join(instance_dir, "config")
    if not os.path.exists(config_dir):
        return None
    for fname in os.listdir(config_dir):
        if fname.startswith("buff_cookies_") and fname.endswith(".txt"):
            fpath = os.path.join(config_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                cookie = f.read().strip()
            if cookie and cookie != "session=":
                return cookie
    return None


def get_proxy(instance_dir):
    """从 config.json5 读取代理设置"""
    config_path = os.path.join(instance_dir, "config", "config.json5")
    if os.path.exists(config_path):
        try:
            config = read_json5_config(config_path)
            if config.get("use_proxies") and "proxies" in config:
                http_proxy = config["proxies"].get("http", "")
                if http_proxy:
                    return {"http": http_proxy, "https": config["proxies"].get("https", http_proxy)}
        except Exception:
            pass
    return None


# ============================================================
# BUFF API 出售历史
# ============================================================

def fetch_buff_sell_history(buff_cookie, proxies=None):
    """从 BUFF API 获取出售历史"""
    session = requests.Session()
    session.headers = {
        "User-Agent": get_ua(),
        "Cookie": buff_cookie,
    }
    if proxies:
        session.proxies = proxies

    all_items = []
    page = 1
    max_pages = 10  # 最多翻10页，避免无限循环

    while page <= max_pages:
        try:
            resp = session.get(
                f"{BUFF_BASE_URL}/api/market/sell_order/history",
                params={"appid": "730", "mode": "1", "page_num": page, "page_size": 50},
                timeout=15,
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            if data.get("code") != "OK":
                break
            items = data.get("data", {}).get("items", [])
            if not items:
                break
            all_items.extend(items)
            # 检查是否有下一页
            total_count = data.get("data", {}).get("total_count", 0)
            total_page = data.get("data", {}).get("total_page", 0)
            if total_page > 0 and page >= total_page:
                break
            if len(all_items) >= total_count:
                break
            page += 1
            time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print(f"  [警告] BUFF API 请求失败: {e}")
            break

    return all_items


def format_buff_order(item, goods_name_cache=None):
    """将 BUFF API 返回的单条出售记录格式化为文本"""
    if goods_name_cache is None:
        goods_name_cache = {}

    lines = []
    lines.append("=" * 47)
    # 订单ID：sell_order_id 或 id
    sell_order_id = item.get('sell_order_id', '') or item.get('id', '')
    lines.append(f"订单ID: {sell_order_id}")
    # 平台订单号：id 字段
    lines.append(f"平台订单号: {item.get('id', '')}")
    # 状态
    lines.append(f"订单状态: {item.get('state_text', '普通出售')}")
    # 时间
    created_at = item.get("created_at", 0)
    if created_at:
        dt = datetime.fromtimestamp(created_at)
        lines.append(f"时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        lines.append("时间: ")
    lines.append("平台: buff")
    # 商品名称：优先从缓存获取，其次从 item 顶层获取，再尝试 asset_info
    goods_id = item.get("goods_id", "")
    goods_name = item.get("market_hash_name", "")
    if not goods_name and goods_id:
        goods_name = goods_name_cache.get(str(goods_id), "")
    if not goods_name:
        # 尝试从 asset_info 中获取（部分 API 版本可能在此处）
        asset = item.get("asset_info", {})
        goods_name = asset.get("market_hash_name", "") or asset.get("name", "")
    lines.append(f"商品名称: {goods_name}")
    # 磨损值：从 asset_info.paintwear 获取
    asset = item.get("asset_info", {})
    paintwear = asset.get("paintwear", "")
    if paintwear is None:
        paintwear = ""
    lines.append(f"磨损值: {paintwear}")
    lines.append(f"商品ID: {goods_id}")
    # 售价
    price_raw = item.get("price", 0)
    try:
        price = float(price_raw)
        if price == int(price):
            price_str = str(int(price))
        else:
            price_str = str(price)
    except (ValueError, TypeError):
        price = 0.0
        price_str = str(price_raw)
    lines.append(f"售价: {price_str}")
    # 手续费
    fee_raw = item.get("fee", 0)
    try:
        fee = float(fee_raw)
    except (ValueError, TypeError):
        fee = 0.0
    if fee == 0 and price > 0:
        fee = round(price * 0.015, 2)
    lines.append(f"手续费: {fee}")
    lines.append(f"净收入: {round(price - fee, 2)}")
    lines.append("-" * 47)
    # 累计金额在此处不填，后续由汇总逻辑统一计算
    lines.append("累计金额: 0")
    lines.append(f"程序版本: {PROGRAM_VERSION}")
    lines.append("=" * 47)
    return "\n".join(lines)


# ============================================================
# 日志解析
# ============================================================

def parse_logs_for_sales(instance_dir):
    """
    从日志文件中解析出售成功记录。
    日志格式示例:
    [2026-06-08 20:47:36] - INFO: [BuffAutoAcceptOffer] 接受报价成功 报价号：xxx
    [2026-06-08 20:47:36] - INFO: 发货平台：网易BUFF 发货饰品：xxx 订单价格：164 元
    """
    logs_dir = os.path.join(instance_dir, "logs")
    if not os.path.exists(logs_dir):
        return []

    sales = []
    # 匹配日志行
    log_pattern = re.compile(
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*?'
        r'(接受报价成功|发货平台|订单价格|accept.*trade|sell.*success)',
        re.IGNORECASE
    )

    for log_file in sorted(glob.glob(os.path.join(logs_dir, "*.log"))):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # 查找接受报价成功的行
        accept_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*?接受报价成功.*?报价号[：:]?\s*(\d+)',
            re.IGNORECASE
        )
        for m in accept_pattern.finditer(content):
            dt_str = m.group(1)
            offer_id = m.group(2)
            sales.append({
                "time": dt_str,
                "tradeofferid": offer_id,
                "platform": "buff",
                "goods_name": "",
                "price": "",
                "source": "log",
            })

        # 查找发货平台 + 饰品名称 + 价格
        goods_pattern = re.compile(
            r'发货平台[：:]\s*([^\n]+).*?'
            r'发货饰品[：:]\s*([^\n]+).*?'
            r'订单价格[：:]\s*([\d.]+)',
            re.DOTALL
        )
        for m in goods_pattern.finditer(content):
            platform = m.group(1).strip()
            goods_name = m.group(2).strip()
            price = m.group(3).strip()

    return sales


# ============================================================
# 生成报告
# ============================================================

def fetch_goods_names(buff_cookie, goods_ids, proxies=None):
    """批量获取 goods_id 对应的商品名称（使用 goods/info 接口）"""
    if not goods_ids:
        return {}
    session = requests.Session()
    session.headers = {
        "User-Agent": get_ua(),
        "Cookie": buff_cookie,
    }
    if proxies:
        session.proxies = proxies

    name_cache = {}
    for gid in goods_ids:
        try:
            resp = session.get(
                f"{BUFF_BASE_URL}/api/market/goods/info",
                params={"game": "csgo", "goods_id": gid},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "OK":
                    gdata = data.get("data", {})
                    name = gdata.get("name") or gdata.get("market_hash_name", "")
                    if name:
                        name_cache[str(gid)] = name
            time.sleep(0.2)
        except Exception:
            pass
    return name_cache


def generate_report(instance_dir, buff_orders, log_sales):
    """生成指定格式的统计报告"""
    steam_info = get_steam_info(instance_dir)
    steam_username = steam_info.get("steam_username", "unknown")
    # 尝试从 buff cookie 文件名获取用户名
    if steam_username == "unknown" or not steam_username:
        config_dir = os.path.join(instance_dir, "config")
        if os.path.exists(config_dir):
            for fname in os.listdir(config_dir):
                m = re.match(r'buff_cookies_(.+)\.txt', fname)
                if m:
                    steam_username = m.group(1)
                    break

    # steam_id：优先从目录名解析，其次从 session 目录获取
    steam_id = "unknown"
    inst_name = os.path.basename(instance_dir)
    m = re.match(r'^.+?_(765611\d{11})$', inst_name)
    if m:
        steam_id = m.group(1)
    else:
        session_dir = os.path.join(instance_dir, "session")
        if os.path.exists(session_dir):
            for fname in os.listdir(session_dir):
                if fname.endswith(".json") or fname.endswith(".txt"):
                    try:
                        with open(os.path.join(session_dir, fname), "r") as f:
                            data = json.load(f)
                            if "steamid" in data:
                                steam_id = data["steamid"]
                                break
                    except Exception:
                        pass

    # 报告文件名
    report_name = f"{steam_username}_{steam_id}.txt"
    report_path = os.path.join(instance_dir, report_name)

    # 有效出售状态：SUCCESS（出售成功）、DELIVERING（待结算）
    VALID_STATES = {"SUCCESS", "DELIVERING"}

    # 优先使用 BUFF API 数据
    if buff_orders:
        # 按 seller_steamid 过滤，只保留当前账号的出售记录
        my_orders = []
        skipped_other = 0
        skipped_invalid = 0
        for item in buff_orders:
            seller_sid = str(item.get("seller_steamid", ""))
            if steam_id != "unknown" and seller_sid and seller_sid != steam_id:
                skipped_other += 1
                continue
            # 过滤无效状态（如 FAIL 买家支付失败、CANCEL 取消等）
            state = item.get("state", "")
            if state and state not in VALID_STATES:
                skipped_invalid += 1
                continue
            my_orders.append(item)

        if skipped_other > 0:
            print(f"  [过滤] 已排除 {skipped_other} 条其他 Steam 账号的出售记录")
        if skipped_invalid > 0:
            print(f"  [过滤] 已排除 {skipped_invalid} 条无效状态的记录（非成功/待结算）")

        if not my_orders:
            report_content = f"# {steam_username}_{steam_id} 出售统计\n"
            report_content += "# 暂无出售记录\n"
            report_content += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            return report_path, 0.0

        # 批量获取商品名称
        goods_ids = set()
        for item in my_orders:
            gid = item.get("goods_id", "")
            if gid:
                goods_ids.add(str(gid))

        buff_cookie = get_buff_cookie(instance_dir)
        proxies = get_proxy(instance_dir)
        goods_name_cache = {}
        if buff_cookie and goods_ids:
            print(f"  [查询] 获取 {len(goods_ids)} 个商品的名称...")
            goods_name_cache = fetch_goods_names(buff_cookie, goods_ids, proxies)
            print(f"  [查询] 获取到 {len(goods_name_cache)} 个商品名称")

        # 生成报告
        final_lines = []
        running = 0.0
        for item in my_orders:
            order_text = format_buff_order(item, goods_name_cache)
            price = float(item.get("price", 0))
            fee = float(item.get("fee", 0))
            if fee == 0 and price > 0:
                fee = round(price * 0.015, 2)
            running += (price - fee)
            order_text = order_text.replace("累计金额: 0", f"累计金额: {running:.2f}")
            final_lines.append(order_text)
            final_lines.append("")
        report_content = "\n".join(final_lines)

    elif log_sales:
        # 仅从日志解析的数据，信息较少
        final_lines = []
        running = 0.0
        for sale in log_sales:
            slines = []
            slines.append("=" * 47)
            slines.append(f"订单ID: {sale.get('tradeofferid', '')}")
            slines.append("平台订单号: ")
            slines.append("订单状态: 普通出售")
            slines.append(f"时间: {sale.get('time', '')}")
            slines.append(f"平台: {sale.get('platform', 'buff')}")
            slines.append(f"商品名称: {sale.get('goods_name', '')}")
            slines.append("磨损值: ")
            slines.append("商品ID: ")
            price = sale.get("price", "")
            try:
                price_f = float(price)
                fee = round(price_f * 0.015, 2)
                running += (price_f - fee)
                slines.append(f"售价: {price_f}")
                slines.append(f"手续费: {fee}")
                slines.append(f"净收入: {round(price_f - fee, 2)}")
            except (ValueError, TypeError):
                slines.append(f"售价: {price}")
                slines.append("手续费: ")
                slines.append("净收入: ")
            slines.append("-" * 47)
            slines.append(f"累计金额: {running:.2f}")
            slines.append(f"程序版本: {PROGRAM_VERSION}")
            slines.append("=" * 47)
            final_lines.append("\n".join(slines))
            final_lines.append("")
        report_content = "\n".join(final_lines)

    else:
        # 无数据
        running = 0.0
        report_content = f"# {steam_username}_{steam_id} 出售统计\n"
        report_content += "# 暂无出售记录\n"
        report_content += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    # 写入文件
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_path, running


# ============================================================
# 实例发现
# ============================================================

def find_all_instances():
    """发现所有实例目录（排除隐藏目录和非实例目录）"""
    accounts_dir = os.path.join(SCRIPT_DIR, "accounts")
    instances = []
    if os.path.exists(accounts_dir):
        for buff_dir in sorted(os.listdir(accounts_dir)):
            buff_path = os.path.join(accounts_dir, buff_dir)
            if not os.path.isdir(buff_path) or buff_dir.startswith("."):
                continue
            for slot_dir in sorted(os.listdir(buff_path)):
                slot_path = os.path.join(buff_path, slot_dir)
                # 实例目录: 非隐藏、有 config 子目录（排除 __pycache__ 等）
                if os.path.isdir(slot_path) and not slot_dir.startswith(".") and not slot_dir.startswith("_"):
                    config_dir = os.path.join(slot_path, "config")
                    if os.path.isdir(config_dir):
                        instances.append(slot_path)
    return instances


def find_buff_instances(buff_num):
    """发现指定 BUFF 号下的所有实例"""
    accounts_dir = os.path.join(SCRIPT_DIR, "accounts")
    buff_path = os.path.join(accounts_dir, str(buff_num))
    instances = []
    if os.path.exists(buff_path):
        for slot_dir in sorted(os.listdir(buff_path)):
            slot_path = os.path.join(buff_path, slot_dir)
            if os.path.isdir(slot_path) and not slot_dir.startswith(".") and not slot_dir.startswith("_"):
                config_dir = os.path.join(slot_path, "config")
                if os.path.isdir(config_dir):
                    instances.append(slot_path)
    return instances


# ============================================================
# 主逻辑
# ============================================================

def stats_instance(instance_dir):
    """统计单个实例"""
    instance_name = os.path.relpath(instance_dir, os.path.join(SCRIPT_DIR, "accounts"))
    print(f"\n{'='*50}")
    print(f"  统计实例: {instance_name}")
    print(f"{'='*50}")

    # 1. 尝试从 BUFF API 获取
    buff_cookie = get_buff_cookie(instance_dir)
    proxies = get_proxy(instance_dir)
    buff_orders = []

    if buff_cookie:
        print(f"  [1/2] 从 BUFF API 获取出售历史...")
        buff_orders = fetch_buff_sell_history(buff_cookie, proxies)
        print(f"  [1/2] 获取到 {len(buff_orders)} 条记录")
    else:
        print(f"  [1/2] 未找到 BUFF cookie，跳过 API 查询")
        print(f"  [1/2] 提示：先运行一次 ./manage.sh first-login <实例> 完成 BUFF 登录")

    # 2. 从日志解析
    print(f"  [2/2] 解析本地日志...")
    log_sales = parse_logs_for_sales(instance_dir)
    print(f"  [2/2] 从日志解析到 {len(log_sales)} 条记录")

    # 3. 生成报告
    report_path, total = generate_report(instance_dir, buff_orders, log_sales)
    print(f"\n  ✓ 报告已生成: {os.path.basename(report_path)}")
    print(f"  ✓ 累计净收入: ¥{total:.2f}")

    return report_path, total


def stats_all():
    """统计所有实例"""
    instances = find_all_instances()
    if not instances:
        print("未找到任何实例目录")
        return

    print(f"共发现 {len(instances)} 个实例\n")
    grand_total = 0.0
    reports = []

    for inst in instances:
        try:
            path, total = stats_instance(inst)
            reports.append(path)
            grand_total += total
        except Exception as e:
            print(f"  ✗ 统计失败: {e}")

    print(f"\n{'='*50}")
    print(f"  全部统计完成")
    print(f"  共 {len(instances)} 个实例，生成 {len(reports)} 份报告")
    print(f"  全部累计净收入: ¥{grand_total:.2f}")
    print(f"{'='*50}")


def stats_buff(buff_num):
    """统计指定 BUFF 号"""
    instances = find_buff_instances(buff_num)
    if not instances:
        print(f"未找到 BUFF 号 {buff_num} 的实例")
        return

    print(f"BUFF 号 {buff_num} 共 {len(instances)} 个实例\n")
    for inst in instances:
        try:
            stats_instance(inst)
        except Exception as e:
            print(f"  ✗ 统计失败: {e}")


def list_reports():
    """列出所有统计文件"""
    instances = find_all_instances()
    if not instances:
        print("未找到任何实例")
        return

    print(f"{'实例':<35} {'统计文件':<45} {'净收入':>10}")
    print("-" * 95)

    grand_total = 0.0
    for inst in instances:
        instance_name = os.path.relpath(inst, os.path.join(SCRIPT_DIR, "accounts"))
        # 查找统计文件
        report_files = []
        for fname in os.listdir(inst):
            fpath = os.path.join(inst, fname)
            # 只统计真实文件（非符号链接），排除 requirements.txt 等源码符号链接
            if os.path.islink(fpath):
                continue
            if fname.endswith(".txt") and fname not in ("nohup.log", "requirements.txt"):
                if not fname.endswith(".log"):
                    report_files.append(fname)

        if report_files:
            for rf in report_files:
                rp = os.path.join(inst, rf)
                # 读取累计金额
                total = 0.0
                try:
                    with open(rp, "r", encoding="utf-8") as f:
                        content = f.read()
                    # 提取最后一个累计金额
                    amounts = re.findall(r'累计金额:\s*([\d.]+)', content)
                    if amounts:
                        total = float(amounts[-1])
                except Exception:
                    pass
                grand_total += total
                print(f"{instance_name:<35} {rf:<45} ¥{total:>8.2f}")
        else:
            print(f"{instance_name:<35} {'(无统计文件)':<45} {'':>10}")

    print("-" * 95)
    print(f"{'总计':>80} ¥{grand_total:>8.2f}")


def show_help():
    print("Steamauto 出售统计脚本")
    print("")
    print("用法:")
    print("  python3 stats.py <实例路径>              # 统计单个实例")
    print("  python3 stats.py --all                   # 统计所有实例")
    print("  python3 stats.py --buff <BUFF号>         # 统计某BUFF号下所有实例")
    print("  python3 stats.py --list                  # 列出所有实例及其统计文件")
    print("")
    print("示例:")
    print("  python3 stats.py accounts/17827629720/azc23232_76561199268318177")
    print("  python3 stats.py --buff 17328515660")
    print("  python3 stats.py --all")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all":
        stats_all()
    elif arg == "--buff":
        if len(sys.argv) < 3:
            print("用法: python3 stats.py --buff <BUFF号>")
            sys.exit(1)
        stats_buff(sys.argv[2])
    elif arg == "--list":
        list_reports()
    elif arg in ("-h", "--help"):
        show_help()
    else:
        # 视为实例路径
        instance_dir = arg
        if not os.path.isabs(instance_dir):
            instance_dir = os.path.join(SCRIPT_DIR, instance_dir)
        if not os.path.isdir(instance_dir):
            print(f"错误: 目录不存在: {instance_dir}")
            sys.exit(1)
        stats_instance(instance_dir)
