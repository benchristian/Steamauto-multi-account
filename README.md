# Steamauto 多账号管理工具集

基于 [Steamauto](https://github.com/Steamauto/Steamauto) 的 BUFF 自动发货多账号管理方案，支持一台机器同时运行 20+ Steam 账号的自动出售发货。

## 项目结构

```
Steamauto-multi-account/
├── manage.sh                          # 多实例管理脚本
├── stats.py                           # 出售记录统计（BUFF API 同步）
├── import_mafile.py                   # maFile 自动导入工具
├── write_account_info.py              # 批量写入账号配置
├── set_passwords.py                   # 批量设置 Steam 密码
├── buff_app_explorer.py               # BUFF APP UI 探查工具
├── Steamauto多账号管理方案.md          # 完整方案文档
├── Steamauto/                         # [submodule] Steamauto 主项目
└── accounts/                          # 账号数据目录（不纳入版本控制）
    └── <BUFF号>/
        └── <steam_username>_<steam_id>/
```

## 快速开始

### 前置条件

- Python 3.8+
- macOS（manage.sh 基于 macOS 开发）
- BUFF 账号已登录

### 克隆仓库

```bash
git clone --recursive https://github.com/benchristian/Steamauto-multi-account.git
cd Steamauto-multi-account
```

### 常用命令一览

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
```

---

## manage.sh — 多实例管理

核心管理脚本，支持对 20+ Steam 实例的批量操作。

### 实例启停

| 命令 | 说明 |
|------|------|
| `./manage.sh start <buff号/实例名>` | 启动单个实例 |
| `./manage.sh start-buff <buff号>` | 启动某 BUFF 号下所有实例 |
| `./manage.sh start-all` | 启动所有实例 |
| `./manage.sh stop <buff号/实例名>` | 停止单个实例 |
| `./manage.sh stop-buff <buff号>` | 停止某 BUFF 号下所有实例 |
| `./manage.sh stop-all` | 停止所有实例 |

### 状态监控

| 命令 | 说明 |
|------|------|
| `./manage.sh status` | 查看所有实例运行状态概览 |
| `./manage.sh status-buff <buff号>` | 查看某 BUFF 号下每个实例的详细状态 |
| `./manage.sh check-login` | 检查所有实例登录状态（正常/需扫码/密码错误/令牌错误/Cookie过期/网络异常） |
| `./manage.sh log <buff号/实例名>` | 实时 tail 查看指定实例的最新日志 |

### 首次登录

| 命令 | 说明 |
|------|------|
| `./manage.sh first-login <buff号/实例名>` | 前台运行单个实例以完成扫码登录 |
| `./manage.sh first-login-buff <buff号>` | 依次前台登录某 BUFF 号下所有实例 |

### 配置管理

| 命令 | 说明 |
|------|------|
| `./manage.sh config <buff号/实例名>` | 用 vim 编辑实例的 `steam_account_info.json5` |
| `./manage.sh rename <buff号/实例名>` | 将实例目录重命名为 `{steam_username}_{steam_id}` 标准格式 |
| `./manage.sh rename-buff <buff号>` | 重命名某 BUFF 号下所有实例目录 |
| `./manage.sh rename-all` | 重命名所有实例目录 |
| `./manage.sh list` | 列出所有已配置的实例 |

### 版本更新

| 命令 | 说明 |
|------|------|
| `./manage.sh update-check` | 检查 Steamauto 是否有新版本（不更新） |
| `./manage.sh update` | 自动停止实例 → 拉取最新源码 → 安装依赖 → 询问是否重启 |

### 目录结构

```
accounts/
├── 17328515660/                              ← BUFF 号
│   ├── rhettholzmeister9237_76561199887280969/   ← {steam_username}_{steam_id}
│   ├── kistotrumm2073_76561199886451134/
│   └── ...
├── 17324473850/
│   ├── kevyncanon8831_76561198752836818/
│   └── ...
└── ...
```

---

## stats.py — 出售记录统计

通过 BUFF API 获取完整出售历史，自动生成统计报告。

### 特性

- **BUFF API 同步**：可追溯到账号所有历史出售记录（BUFF 服务端永久保存）
- **SteamID 过滤**：同一 BUFF 号下的多个 Steam 账号互不串记录
- **状态过滤**：只统计「出售成功」和「待结算」的有效订单，排除「买家支付失败」「已取消」
- **手续费扣除**：净收入已扣除 BUFF 手续费（优先使用 BUFF 实际手续费，无数据时按 1.5% 估算）
- **双重记录**：Steamauto 插件实时写入 + API 全量同步，数据可靠
- **同一报价多件商品**：插件已修复，同一买家同时购买多件相同装备也能逐条记录
- **每日自动同步**：已配置凌晨 00:00 自动运行 `stats.py --all`

### 用法

```bash
# 统计单个实例
python3 stats.py accounts/<BUFF号>/<实例名>

# 统计所有实例
python3 stats.py --all

# 统计某 BUFF 号下所有实例
python3 stats.py --buff <BUFF号>

# 查看汇总
python3 stats.py --list

# 通过 manage.sh 调用
./manage.sh stats <buff号/实例名>
./manage.sh stats-buff <buff号>
./manage.sh stats-all
./manage.sh stats-list
```

### 统计文件格式

每笔订单包含完整的出售信息，末尾自动计算累计金额：

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
程序版本: 5.8.6
===============================================
```

---

## 账号配置工具

### import_mafile.py — maFile 导入

从 steam-desktop-authenticator 的 maFile 目录自动导入 `shared_secret` 和 `identity_secret`，写入实例的 `steam_account_info.json5`。

```bash
python3 import_mafile.py [--accounts-dir <path>] [--mafiles-dir <path>]

# 通过 manage.sh 调用
./manage.sh import-mafile [--accounts-dir <path>] [--mafiles-dir <path>]
```

**原理**：从实例目录名 `{steam_username}_{steam_id}` 解析出 `steam_id`，在 maFile 目录中匹配对应文件，读取令牌密钥后写入配置。

### write_account_info.py — 批量写入配置

从 CSV 文件和 maFile 目录批量生成完整的 `steam_account_info.json5`。

```bash
python3 write_account_info.py [--csv <csv文件>] [--mafiles-dir <maFile目录>] [--dry-run]
```

**数据来源**：
- CSV 文件：`steam_username`、`steam_password`
- maFile 目录：`shared_secret`、`identity_secret`

支持 `--dry-run` 预览模式，先查看将要写入的内容再执行。

### set_passwords.py — 批量设置密码

从 CSV 文件读取密码，批量写入到已有实例的 `steam_account_info.json5` 中。

```bash
python3 set_passwords.py [csv文件路径]
```

---

## buff_app_explorer.py — BUFF APP UI 探查

通过 ADB 连接模拟器上的 BUFF APP，dump 当前界面的 UI 元素结构，用于开发调试时定位按钮和页面元素。

```bash
python buff_app_explorer.py
```

**使用步骤**：
1. 在模拟器上打开 BUFF APP 并登录
2. 手动导航到目标页面
3. 运行脚本 dump UI 结构

---

## Steamauto Submodule

本项目将 Steamauto 作为 git submodule 管理，可独立跟踪上游更新：

```bash
# 更新 submodule 到最新
cd Steamauto && git pull origin master

# 或通过 manage.sh（自动停止实例 → 拉取 → 安装依赖 → 重启）
./manage.sh update
```

---

## 目录结构约定

每个实例目录的标准结构：

```
accounts/<BUFF号>/<steam_username>_<steam_id>/
├── config/
│   ├── steam_account_info.json5    # Steam 账号配置（用户名、密码、令牌密钥）
│   └── buff_cookies_*.txt          # BUFF 登录 Cookie
├── session/                        # Steam 会话文件
├── logs/                           # 运行日志
├── pid.txt                         # 进程 PID（manage.sh 管理用）
├── nohup.log                       # 后台运行输出
└── <steam_username>_<steam_id>.txt # 出售记录统计文件
```

## 许可

本项目为 Steamauto 的配套管理工具集，遵循与原项目相同的许可协议。
