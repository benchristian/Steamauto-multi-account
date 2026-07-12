# Steamauto 多账号自动发货管理方案 (macOS)

> 基于 [Steamauto](https://github.com/RuokReally/Steamauto) 的多实例部署方案  
> 支持 1 台 Mac 同时运行多个 BUFF 账号的自动发货

---

## 一、目录结构

```
Steamauto多账号/
├── Steamauto/                      # 唯一源码（git pull 即更新所有实例）
│   ├── Steamauto.py
│   ├── utils/  steampy/  BuffApi/  plugins/  ...
│   ├── config/                     # 模板配置（首次部署参考用）
│   └── requirements.txt
├── accounts/                       # 所有实例的用户数据
│   ├── 17328515660/                # 会员BUFF号（可开多个Steam实例）
│   │   ├── myaccount_76561191234567890/  # 实例目录: {steam用户名}_{steam_id}
│   │   │   ├── Steamauto.py  -> ../../../Steamauto/Steamauto.py  (符号链接)
│   │   │   ├── utils/        -> ../../../Steamauto/utils/
│   │   │   ├── steampy/      -> ../../../Steamauto/steampy/
│   │   │   ├── BuffApi/      -> ... (所有源码均为符号链接)
│   │   │   ├── config/               # 【独立】配置文件、Cookie
│   │   │   ├── session/              # 【独立】Steam 登录会话
│   │   │   ├── logs/                 # 【独立】运行日志
│   │   │   ├── pid.txt               # 进程 PID
│   │   │   └── nohup.log             # 后台运行日志
│   │   ├── another_76561199876543210/ # 同上结构
│   ├── 13242040227/azc23232_76561199268318177/  # 普通BUFF号（各1个实例）
│   ├── ...（共10个BUFF号，20个实例）
└── manage.sh                       # 多账号管理脚本
```

**实例目录命名规则：`{steam_username}_{steam_id}`**

**总计：20 个实例**（1个会员 × 10实例 + 1个普通 × 2实例 + 8个普通 × 1实例）

---

## 二、环境准备

### 2.1 安装 Python 依赖

```bash
# 安装 Python 3（macOS 自带）
python3 --version

# 安装依赖
pip3 install -r Steamauto/requirements.txt

# macOS 下修复 LibreSSL 兼容性问题
pip3 install urllib3==1.26.18
```

### 2.2 检测代理端口

```bash
# 方法1：查看系统代理设置
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi

# 方法2：查看 Clash/V2Ray 监听端口
lsof -i -P | grep LISTEN | grep -E 'clash|v2ray|xray'
```

记录代理地址，例如 `http://127.0.0.1:10900`，后续填入 `config.json5`。

---

## 三、配置文件

### 3.1 `config/config.json5`（主配置）

```json5
{
  "steam_login_ignore_ssl_error": false,
  "steam_local_accelerate": false,

  // 【重要】启用代理
  "use_proxies": true,
  "proxies": {
    "http": "http://127.0.0.1:10900",    // 改成你的代理端口
    "https": "http://127.0.0.1:10900"
  },

  "notify_service": {
    "notifiers": [],
    "custom_title": "",
    "include_steam_info": true,
    "blacklist_words": []
  },

  // 【核心】BUFF 自动发货
  "buff_auto_accept_offer": {
    "enable": true,
    "interval": 300,        // 轮询间隔（秒），建议 180-300
    "dota2_support": false,
    "use_proxies": false    // BUFF走直连，不走代理
  },

  "uu_auto_accept_offer": {
    "enable": false,
    "interval": 300,
    "use_proxies": false
  },

  "uu_auto_lease_item": {
    "enable": false,
    "lease_max_days": 60,
    "filter_price": 100,
    "run_time": "17:30",
    "interval": 31,
    "filter_name": [],
    "enable_fix_lease_ratio": false,
    "fix_lease_ratio": 0.001,
    "compensation_type": 7
  },

  "uu_auto_sell_item": {
    "enable": false,
    "take_profile": false,
    "take_profile_ratio": 0.1,
    "run_time": "15:30",
    "sell_interval": 20,
    "max_on_sale_price": 1000,
    "interval": 51,
    "name": [],
    "blacklist_words": [],
    "use_price_adjustment": true,
    "price_adjustment_threshold": 1.0
  },

  "steam_auto_accept_offer": {
    "enable": false,
    "interval": 300
  },

  "ecosteam": {
    "enable": false,
    "partnerId": "",
    "auto_accept_offer": { "interval": 30 },
    "auto_sync_sell_shelf": {
      "enable": false,
      "main_platform": "eco",
      "enabled_platforms": ["uu"],
      "ratio": { "eco": 1, "uu": 1, "buff": 1 }
    },
    "auto_sync_lease_shelf": {
      "enable": false,
      "main_platform": "eco",
      "ratio": { "eco": 1, "uu": 1 }
    },
    "sync_interval": 60,
    "qps": 10
  },

  "c5_auto_accept_offer": {
    "enable": false,
    "interval": 30,
    "app_key": ""
  },

  "log_level": "debug",
  "log_retention_days": 7,
  "no_pause": false,
  "plugin_whitelist": [],
  "source_code_auto_update": false
}
```

### 3.2 `config/steam_account_info.json5`（Steam 账号）

```json5
{
  // Steam 令牌 shared_secret（从 Steam 手机令牌获取）
  "shared_secret": "你的shared_secret",

  // Steam 令牌 identity_secret（从 Steam 手机令牌获取）
  "identity_secret": "你的identity_secret",

  // Steam 登录用户名
  "steam_username": "你的steam用户名",

  // Steam 登录密码
  "steam_password": "你的steam密码"
}
```

> **获取令牌的方法**：参考 Steamauto 项目文档，从 Steam 手机 App 的令牌文件中提取。

---

## 四、管理脚本 `manage.sh`

源码见仓库中的 `manage.sh` 文件，下面按功能分类介绍所有命令。

### 4.1 实例启停

| 命令 | 说明 |
|------|------|
| `start <buff号/实例名>` | 启动指定实例 |
| `start-buff <buff号>` | 启动某BUFF号下所有实例 |
| `start-all` | 启动所有实例 |
| `stop <buff号/实例名>` | 停止指定实例 |
| `stop-buff <buff号>` | 停止某BUFF号下所有实例 |
| `stop-all` | 停止所有实例 |

### 4.2 状态与监控

| 命令 | 说明 |
|------|------|
| `status` | 查看所有实例运行状态 |
| `status-buff <buff号>` | 查看某BUFF号下所有实例状态 |
| `check-login` | 检查所有实例的登录状态（是否登录失效、Cookie过期等），自动分析日志判断异常原因 |
| `list` | 列出所有已配置的实例 |

### 4.3 首次登录

| 命令 | 说明 |
|------|------|
| `first-login <buff号/实例名>` | 前台运行以完成首次扫码登录 |
| `first-login-buff <buff号>` | 依次前台登录某BUFF号所有实例 |

### 4.4 配置管理

| 命令 | 说明 |
|------|------|
| `config <buff号/实例名>` | 用 vim 编辑指定实例的 `steam_account_info.json5` |
| `rename <buff号/实例名>` | 按 `{steam_username}_{steam_id}` 格式重命名实例目录 |
| `rename-buff <buff号>` | 重命名某BUFF号下所有实例目录 |
| `rename-all` | 重命名所有实例目录 |

### 4.5 统计

| 命令 | 说明 |
|------|------|
| `stats <buff号/实例名>` | 统计指定实例的出售记录（调用 BUFF API） |
| `stats-buff <buff号>` | 统计某BUFF号下所有实例的出售记录 |
| `stats-all` | 统计所有实例的出售记录 |
| `stats-list` | 列出所有统计文件 |

### 4.6 源码更新

| 命令 | 说明 |
|------|------|
| `update` | 一键更新：自动停止→git pull→安装依赖→询问重启 |
| `update-check` | 仅检查 Steamauto 是否有新版本 |

### 4.7 账号导入

| 命令 | 说明 |
|------|------|
| `import-mafile` | 从 steam-desktop-authenticator 导入 maFile 配置 |
| `import-mafile --dry-run` | 仅预览匹配结果，不实际写入 |
| `import-mafile --dry-run --auto-skip` | 自动跳过未匹配的 maFile |

### 4.8 查看日志

| 命令 | 说明 |
|------|------|
| `log <buff号/实例名>` | 实时 tail -f 指定实例的最新日志 |

> **注意**：所有后台启动的实例使用 `caffeinate -i` 包裹，防止 macOS 休眠，且通过 `nohup` 运行，关闭终端不影响进程。

---

## 五、操作指南

### 5.1 首次部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/Steamauto/Steamauto.git
cd Steamauto多账号/

# 2. 安装依赖
pip3 install -r Steamauto/requirements.txt
pip3 install urllib3==1.26.18   # macOS 兼容修复

# 3. 创建实例目录（以 17827629720/azc23232_76561199268318177 为例）
BUFF_NUM="17827629720"
INST_NAME="azc23232_76561199268318177"
INST_DIR="accounts/$BUFF_NUM/$INST_NAME"
mkdir -p "$INST_DIR/config" "$INST_DIR/session" "$INST_DIR/logs"

# 4. 创建源码符号链接
cd "$INST_DIR"
SRC="../../../Steamauto"
ln -s "$SRC/Steamauto.py" Steamauto.py
ln -s "$SRC/BuffApi" BuffApi
ln -s "$SRC/plugins" plugins
ln -s "$SRC/protobufs" protobufs
ln -s "$SRC/PyC5Game" PyC5Game
ln -s "$SRC/PyECOsteam" PyECOsteam
ln -s "$SRC/steampy" steampy
ln -s "$SRC/utils" utils
ln -s "$SRC/uuyoupinapi" uuyoupinapi
cd ../../..

# 5. 写入配置文件
cp Steamauto/config/config.json5 "$INST_DIR/config/"
cp Steamauto/config/steam_account_info.json5 "$INST_DIR/config/"
# 编辑 $INST_DIR/config/config.json5（代理设置）
# 编辑 $INST_DIR/config/steam_account_info.json5（Steam信息）

# 6. 首次扫码登录（前台运行）
./manage.sh first-login "$BUFF_NUM/$SLOT"

# 7. 后台启动
./manage.sh start "$BUFF_NUM/$SLOT"
```

### 5.2 日常管理命令

```bash
# 查看所有实例
./manage.sh list

# 查看运行状态
./manage.sh status

# 启动全部
./manage.sh start-all

# 停止全部
./manage.sh stop-all

# 启动某个 BUFF 号的所有实例
./manage.sh start-buff 17328515660

# 停止某个 BUFF 号的所有实例
./manage.sh stop-buff 17328515660

# 启动/停止单个实例
./manage.sh start 17827629720/azc23232_76561199268318177
./manage.sh stop 17827629720/azc23232_76561199268318177

# 编辑 Steam 配置
./manage.sh config 17827629720/azc23232_76561199268318177

# 查看日志
./manage.sh log 17827629720/azc23232_76561199268318177

# 将实例目录重命名为 {steam_username}_{steam_id} 格式
./manage.sh rename 17827629720/steam_01
./manage.sh rename-buff 17328515660   # 重命名某BUFF号下所有实例
./manage.sh rename-all                # 重命名所有实例

# 检查 Steamauto 是否有更新
./manage.sh update-check

# 一键更新 Steamauto 源码（自动停止→拉取→安装依赖→询问重启）
./manage.sh update

# ======= 出售统计 =======

# 统计单个实例（调用 BUFF API 获取出售历史）
./manage.sh stats 17827629720/azc23232_76561199268318177

# 统计某 BUFF 号下所有实例
./manage.sh stats-buff 17328515660

# 统计所有实例
./manage.sh stats-all

# 列出所有统计文件
./manage.sh stats-list

# ======= MaFile 导入 =======

# 从 steam-desktop-authenticator 导入 maFile 配置到 steam_account_info.json5
./manage.sh import-mafile

# 仅预览匹配结果，不实际写入
./manage.sh import-mafile --dry-run

# 自动跳过未匹配的 maFile（不进入交互模式）
./manage.sh import-mafile --dry-run --auto-skip
```


### 5.2.1 出售统计说明

`stats` 命令会在实例目录下生成统计文件，文件命名格式为：
```
<steam_username>_<steam_id>.txt
```

**双重记录机制：**

1. **实时记录** — Steamauto 插件每卖出一件装备，自动追加到统计文件
2. **API 同步** — 随时可运行 `stats` 命令，从 BUFF API 拉取完整历史并覆盖本地文件

**数据来源优先级：**
1. **BUFF API 出售历史** — 通过 `buff_cookies_*.txt` 中的 cookie 调用 BUFF API 获取完整出售记录（需先完成 BUFF 登录）
2. **本地日志解析** — 从 `logs/` 目录的日志文件中提取发货记录（信息不如 API 完整）

**BUFF API 同步的特点：**
- 可追溯到账号所有历史出售记录（BUFF 服务端永久保存）
- 自动按 `seller_steamid` 过滤，同一 BUFF 号下的多个 Steam 账号不会串记录
- **只统计有效订单**：`出售成功` 和 `待结算` 状态的订单，`买家支付失败`、`已取消` 等无效订单自动排除
- 净收入已扣除手续费（优先使用 BUFF 实际手续费，无数据时按 1.5% 估算）
- 每笔订单自动计算累计金额

**统计文件格式：**
```
===============================================
订单ID: 9146544673
平台订单号: 260608T3717151792
订单状态: 出售成功
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

**定期同步建议：** 每隔一段时间运行 `./manage.sh stats-all`，确保出售记录与 BUFF 服务端一致，补齐任何漏掉的记录。

### 5.3 更换 Steam 账号流程

当一个 BUFF 实例需要换绑新的 Steam 号时：

```bash
# 1. 停止该实例
./manage.sh stop 17827629720/azc23232_76561199268318177

# 2. 修改 Steam 配置
./manage.sh config 17827629720/azc23232_76561199268318177
# 修改 shared_secret, identity_secret, steam_username, steam_password

# 3. 删除旧的 BUFF Cookie（重要！否则会用旧账号的BUFF登录态）
rm accounts/17827629720/azc23232_76561199268318177/config/buff_cookies_*.txt

# 4. 重新扫码登录 BUFF
./manage.sh first-login 17827629720/azc23232_76561199268318177

# 5. 后台启动
./manage.sh start 17827629720/azc23232_76561199268318177
```

### 5.4 新增 BUFF 号（或实例）

```bash
BUFF_NUM="新BUFF号"
# 实例目录名格式: {steam_username}_{steam_id}
INST_NAME="steam用户名_steamid"
INST_DIR="accounts/$BUFF_NUM/$INST_NAME"
mkdir -p "$INST_DIR/config" "$INST_DIR/session" "$INST_DIR/logs"

# 创建符号链接
cd "$INST_DIR"
SRC="../../../Steamauto"
ln -s "$SRC/Steamauto.py" Steamauto.py
ln -s "$SRC/BuffApi" BuffApi
ln -s "$SRC/plugins" plugins
ln -s "$SRC/protobufs" protobufs
ln -s "$SRC/PyC5Game" PyC5Game
ln -s "$SRC/PyECOsteam" PyECOsteam
ln -s "$SRC/steampy" steampy
ln -s "$SRC/utils" utils
ln -s "$SRC/uuyoupinapi" uuyoupinapi
cd ../../..

# 写入配置模板
cp Steamauto/config/config.json5 "$INST_DIR/config/"
cp Steamauto/config/steam_account_info.json5 "$INST_DIR/config/"

# 编辑配置文件
# vim $INST_DIR/config/config.json5（代理设置）
# vim $INST_DIR/config/steam_account_info.json5（Steam信息）

# 首次登录 + 启动
./manage.sh first-login "$BUFF_NUM/$SLOT"
./manage.sh start "$BUFF_NUM/$SLOT"
```

---

## 六、当前 BUFF 号清单

| BUFF号 | 类型 | 实例数 | 实例目录 |
|--------|------|--------|---------|
| 17328515660 | 会员 | 10 | `beatrizjeskie354_76561199887510217` 等 |
| 17324473850 | 普通 | 2 | `kevyncanon8831_76561198752836818`、`qdw565643_76561199267633747` |
| 13510278160 | 普通 | 1 | `dzcz15563_76561199267444173` |
| 13242040227 | 普通 | 1 | `azc23232_76561199268318177` |
| 13265677880 | 普通 | 1 | `3kknmd6avwc_76561198793206061` |
| 15362053264 | 普通 | 1 | `hjaz23256_76561199268040010` |
| 15813347556 | 普通 | 1 | `jjuo78954_76561199267984161` |
| 17724562830 | 普通 | 1 | `zxxv65561_76561199268072990` |
| 17818370030 | 普通 | 1 | `encinobriede18_76561198784895255` |
| 17827629720 | 普通 | 1 | `zxzc45651_76561199267959894` |

**总计：20 个实例**

---

## 七、关键说明

### 源码共享
所有 20 个实例通过**符号链接**共享 `Steamauto/` 目录下的源码。更新源码只需：

```bash
./manage.sh update    # 一键完成：停止→git pull→安装依赖→重启
```

### 共享与隔离对照

| 目录/文件 | 类型 | 说明 |
|-----------|------|------|
| `config/` | 独立数据 | 每个实例的配置、Cookie、令牌，**不可共享** |
| `session/` | 独立数据 | Steam 登录会话，**不可共享** |
| `logs/` | 独立数据 | 运行日志，**不可共享** |
| `nohup.log` | 独立数据 | 后台运行日志 |
| `pid.txt` | 独立数据 | 进程 PID |
| `Steamauto.py` | 符号链接 → 源码 | 主入口 |
| `utils/` `steampy/` `BuffApi/` `plugins/` 等 | 符号链接 → 源码 | 共享代码 |

> **核心原则**：凡是 Steamauto 项目自带的文件/目录都做成符号链接，凡是运行时产生的用户数据都保留为真实目录。

### 防休眠
管理脚本使用 `caffeinate -i` 包裹 Python 进程，防止 macOS 在运行期间进入休眠。即使关闭终端，后台进程也会继续运行。

### BUFF Cookie 隔离
每个实例的 BUFF 登录态存储为 `config/buff_cookies_{steam_username}.txt`，按 Steam 用户名区分，因此不同实例的登录态互不干扰。

### 代理配置
- Steam 连接走代理（`use_proxies: true`）
- BUFF 建议走直连（`buff_auto_accept_offer.use_proxies: false`）
- 代理地址根据你的 Clash/V2Ray 端口填写

### 关闭终端后继续运行
所有通过 `./manage.sh start` 启动的实例使用 `nohup` 后台运行，关闭终端不影响进程。重启 Mac 后需要重新执行 `./manage.sh start-all`。

---

## 八、批量写入 steam_account_info.json5

一次性为所有实例写入完整的 Steam 账号信息（shared_secret、identity_secret、steam_username、steam_password）：

```bash
# 预览匹配结果（不实际写入）
python3 write_account_info.py --dry-run

# 正式写入
python3 write_account_info.py
```

**数据来源：**
- `steam账号.csv` → `steam_username`、`steam_password`
- `steam-desktop-authenticator/maFiles/` → `shared_secret`、`identity_secret`
- 实例目录名 `{username}_{steam_id}` → 关联 CSV 与 maFile

**可选参数：**
```bash
python3 write_account_info.py --csv 自定义.csv --mafiles-dir /path/to/maFiles --accounts-dir ./accounts
```

---

## 九、故障排查

```bash
# 查看某个实例的后台日志
cat accounts/17827629720/zxzc45651_76561199267959894/nohup.log

# 查看 Steamauto 运行日志
tail -f accounts/17827629720/zxzc45651_76561199267959894/logs/*.log

# 手动杀掉残留进程
kill $(cat accounts/17827629720/zxzc45651_76561199267959894/pid.txt)

# 清理所有 PID 文件（如果状态显示异常）
find accounts -name "pid.txt" -delete

# 检查符号链接是否完好
find accounts -type l -exec test ! -e {} \; -print

# 检查所有实例的登录状态（是否登录失效）
./manage.sh check-login
```
