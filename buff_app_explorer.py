#!/usr/bin/env python3
"""
BUFF APP UI 探查脚本
用于 dump BUFF APP 的界面元素结构，帮助定位「发起报价」等按钮

使用方法:
1. 在模拟器上打开 BUFF APP 并登录
2. 手动导航到你想探查的页面（如「我卖出的」列表页）
3. 运行: python buff_app_explorer.py
"""

import uiautomator2 as u2
import json
import os
import sys
import time


def explore_buff_app(device_serial="127.0.0.1:7555"):
    """探查 BUFF APP 当前界面的 UI 结构"""
    
    print(f"[*] 连接设备: {device_serial}")
    try:
        d = u2.connect(device_serial)
        print(f"[+] 设备连接成功: {d.info}")
    except Exception as e:
        print(f"[-] 连接失败: {e}")
        print("[!] 请确保模拟器已启动并开启了 ADB 调试")
        print("[!] Mumu 模拟器默认 ADB 地址: 127.0.0.1:7555")
        print("[!] 雷电模拟器默认 ADB 地址: 127.0.0.1:5555")
        sys.exit(1)
    
    # 获取当前运行的 APP
    current = d.app_current()
    print(f"\n[*] 当前前台 APP:")
    print(f"    package: {current['package']}")
    print(f"    activity: {current.get('activity', 'unknown')}")
    
    # 判断是否是 BUFF APP
    if "buff" not in current['package'].lower():
        print("\n[!] 当前不是 BUFF APP，请先打开 BUFF APP 并导航到目标页面")
        return
    
    # 截图保存
    screenshot_dir = os.path.join(os.path.dirname(__file__), "buff_ui_screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"buff_{timestamp}.png")
    d.screenshot(screenshot_path)
    print(f"\n[+] 截图已保存: {screenshot_path}")
    
    # Dump UI 层级
    xml_path = os.path.join(screenshot_dir, f"buff_{timestamp}.xml")
    xml_content = d.dump_hierarchy()
    
    # 保存原始 XML
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"[+] UI 层级 XML 已保存: {xml_path}")
    
    # 解析并提取关键信息
    print("\n" + "=" * 60)
    print("📱 BUFF APP UI 元素分析")
    print("=" * 60)
    
    # 查找所有可点击的元素
    clickable = []
    for elem in d(clickable=True):
        try:
            info = {
                "text": elem.get_text() or "",
                "desc": elem.info.get("contentDescription", "") or "",
                "class": elem.info.get("className", ""),
                "resourceId": elem.info.get("resourceId", ""),
                "bounds": elem.info.get("bounds", {}),
                "package": elem.info.get("packageName", ""),
            }
            # 只保留有文本或描述的
            if info["text"] or info["desc"]:
                clickable.append(info)
        except Exception:
            pass
    
    print(f"\n找到 {len(clickable)} 个有文本的可点击元素:\n")
    
    for i, elem in enumerate(clickable):
        text_or_desc = elem["text"] or elem["desc"]
        rid = elem["resourceId"].split("/")[-1] if elem["resourceId"] else "N/A"
        bounds = elem["bounds"]
        print(f"  [{i}] text/desc: '{text_or_desc}'")
        print(f"      resourceId: {rid}")
        print(f"      class: {elem['class'].split('.')[-1]}")
        print(f"      bounds: {bounds}")
        print()
    
    # 专门搜索关键词
    keywords = ["发起报价", "报价", "出售", "卖出", "订单", "我的", "切换账号", "登录"]
    print("=" * 60)
    print("🔍 关键词搜索:")
    print("=" * 60)
    
    for kw in keywords:
        matches = []
        for elem in d(textContains=kw):
            try:
                bounds = elem.info.get("bounds", {})
                matches.append({
                    "text": elem.get_text(),
                    "bounds": bounds,
                })
            except Exception:
                pass
        
        if matches:
            print(f"\n  关键词 '{kw}' 匹配到 {len(matches)} 个元素:")
            for m in matches[:5]:  # 最多显示5个
                print(f"    - '{m['text']}' @ {m['bounds']}")
    
    print("\n" + "=" * 60)
    print("[*] 探查完成！")
    print(f"[*] 截图: {screenshot_path}")
    print(f"[*] XML: {xml_path}")
    print("\n[!] 提示：请在不同页面（首页、我的、我卖出的、订单详情）")
    print("    分别运行此脚本，收集完整的 UI 结构信息")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BUFF APP UI 探查工具")
    parser.add_argument(
        "--device", "-d",
        default="127.0.0.1:7555",
        help="ADB 设备序列号或地址 (默认: 127.0.0.1:7555, Mumu模拟器)"
    )
    args = parser.parse_args()
    
    explore_buff_app(args.device)
