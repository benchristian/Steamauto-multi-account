# Steamauto 多账号管理工具集

基于 [Steamauto](https://github.com/Steamauto/Steamauto) 的 BUFF 自动发货多账号管理方案，支持一台机器同时运行 20+ Steam 账号的自动出售发货。

## 项目结构

```
Steamauto-multi-account/
├── manage.sh                          # 多实例管理脚本（启动/停止/状态/日志）
├── stats.py                           # 出售记录统计（BUFF API 同步）
├── import_mafile.py                   # maFile 导入工具
├── write_account_info.py              # 账号配置写入工具
├── set_passwords.py                   # 批量设置密码
├── buff_app_explorer.py               # BUFF 商品浏览工具
├── Steamauto多账号管理方案.md          # 完整方案文档
├── Steamauto/                         # [submodule] Steamauto 主项目
└── accounts/                          # 账号数据目录（不纳入版本控制）
    └── <BUFF号>/
        └── <steam_username>_<steam_id>/
```

## 快速开始

### 前置条件

- Python 3.8+
- [Steamauto](https://github.com/Steamauto/Steamauto) 已配置
- BUFF 账号已登录

### 克隆仓库

```bash
git clone --recursive https://github.com/benchristian/Steamauto-multi-account.git
cd Steamauto-multi-account
```

### 常用命令

```bash
# 启动所有实例
./manage.sh start-all

# 查看运行状态
./manage.sh status

# 停止所有实例
./manage.sh stop-all

# 拉取 Steamauto 最新源码并重启
./manage.sh update

# 同步所有账号出售记录（从 BUFF API）
./manage.sh stats-all

# 查看出售记录汇总
./manage.sh stats-list
```

## 出售记录统计

`stats.py` 通过 BUFF API 获取完整出售历史，自动生成统计报告。

### 特性

- **BUFF API 同步**：可追溯到账号所有历史出售记录
- **SteamID 过滤**：同一 BUFF 号下的多个 Steam 账号互不串记录
- **状态过滤**：只统计「出售成功」和「待结算」的有效订单，排除「买家支付失败」「已取消」
- **手续费扣除**：净收入已扣除 BUFF 手续费
- **双重记录**：插件实时写入 + API 全量同步，数据可靠

### 用法

```bash
# 统计单个实例
python3 stats.py accounts/<BUFF号>/<实例名>

# 统计所有实例
python3 stats.py --all

# 查看汇总
python3 stats.py --list

# 通过 manage.sh 调用
./manage.sh stats-all
```

### 统计文件格式

```
===============================================
订单ID: 260608T3717151792
平台订单号: 260608T3717151792
订单状态: 待 07-19 14:00 结算
时间: 2026-06-08 20:47:36
平台: buff
商品名称: FN57 | 同步力场 (崭新出厂)
磨损值: 0.03815452381968498
商品ID: 871429
售价: 164
手续费: 2.47
净收入: 161.53
-----------------------------------------------
累计金额: 161.53
程序版本: 3.18
===============================================
```

## Steamauto Submodule

本项目将 Steamauto 作为 git submodule 管理，可独立跟踪上游更新：

```bash
# 更新 submodule 到最新
cd Steamauto && git pull origin master

# 或通过 manage.sh
./manage.sh update
```

## 许可

本项目为 Steamauto 的配套管理工具集，遵循与原项目相同的许可协议。
