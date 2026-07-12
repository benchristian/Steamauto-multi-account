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
│   ├── ...（共10个BUFF号，19个实例）
└── manage.sh                       # 多账号管理脚本
```

**实例目录命名规则：`{steam_username}_{steam_id}`**

**总计：19 个实例**（1个会员 × 10实例 + 9个普通 × 1实例）

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

```bash
#!/bin/bash
# ============================================
# Steamauto 多账号管理脚本 v2 (macOS)
# 支持二级目录: accounts/BUFF号/<steam用户名>_<steam_id>/
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STEAMAUTO_DIR="$SCRIPT_DIR/Steamauto"
ACCOUNTS_DIR="$SCRIPT_DIR/accounts"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo -e "${CYAN}============================================"
    echo "  Steamauto 多账号管理工具 v2"
    echo -e "============================================${NC}"
    echo ""
    echo "用法: ./manage.sh <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  start <buff号/实例名>  启动指定实例"
    echo "  start-buff <buff号>    启动某BUFF号下所有实例"
    echo "  start-all              启动所有实例"
    echo "  stop <buff号/实例名>   停止指定实例"
    echo "  stop-buff <buff号>     停止某BUFF号下所有实例"
    echo "  stop-all               停止所有实例"
    echo "  status                 查看所有实例运行状态"
    echo "  status-buff <buff号>   查看某BUFF号下所有实例状态"
    echo "  config <buff号/实例名> 编辑指定实例的Steam配置"
    echo "  log <buff号/实例名>    实时查看指定实例日志"
    echo "  list                   列出所有实例"
    echo "  first-login <buff号/实例名> 前台运行以完成首次扫码登录"
    echo "  first-login-buff <buff号> 依次前台登录某BUFF号所有实例"
    echo "  rename <buff号/实例名> 按 {steam_username}_{steam_id} 格式重命名实例目录"
    echo "  rename-buff <buff号>   重命名某BUFF号下所有实例目录"
    echo "  rename-all             重命名所有实例目录"
    echo "  import-mafile          从 steam-desktop-authenticator 导入 maFile 配置"
    echo ""
    echo "目录结构示例:"
    echo "  accounts/17827629720/azc23232_76561199268318177/  ← BUFF号/Steam用户名_SteamID"
    echo "  accounts/17328515660/myaccount_76561191234567890/  ← 会员BUFF可开多实例"
    echo "  accounts/17328515660/another_76561199876543210/"
    echo "  ..."
    echo ""
}

# ============================================
# 解析参数: "buff号/实例名" -> BUFF_NUM INSTANCE_NAME
# ============================================
parse_target() {
    local target=$1
    if [[ "$target" == *"/"* ]]; then
        BUFF_NUM="${target%%/*}"
        INSTANCE_NAME="${target##*/}"
    else
        BUFF_NUM="$target"
        INSTANCE_NAME=""
    fi
}

get_instance_dir() {
    local buff=$1
    local slot=$2
    echo "$ACCOUNTS_DIR/$buff/$slot"
}

# ============================================
# 启动单个实例
# ============================================
start_instance() {
    local buff=$1
    local slot=$2
    local inst_dir=$(get_instance_dir "$buff" "$slot")
    local label="$buff/$slot"

    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $label 不存在${NC}"
        return 1
    fi

    if [ -f "$inst_dir/pid.txt" ]; then
        local old_pid=$(cat "$inst_dir/pid.txt")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo -e "${YELLOW}$label 已在运行中 (PID: $old_pid)${NC}"
            return 0
        fi
    fi

    cd "$inst_dir"
    nohup caffeinate -i python3 Steamauto.py > "$inst_dir/nohup.log" 2>&1 &
    local pid=$!
    echo $pid > "$inst_dir/pid.txt"
    sleep 2

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $label ${GREEN}已启动${NC} (PID: $pid)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $label ${RED}启动失败${NC}"
        return 1
    fi
}

# ============================================
# 停止单个实例
# ============================================
stop_instance() {
    local buff=$1
    local slot=$2
    local inst_dir=$(get_instance_dir "$buff" "$slot")
    local label="$buff/$slot"

    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $label 不存在${NC}"
        return 1
    fi

    if [ ! -f "$inst_dir/pid.txt" ]; then
        return 0
    fi

    local pid=$(cat "$inst_dir/pid.txt")
    if ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$inst_dir/pid.txt"
        return 0
    fi

    kill "$pid" 2>/dev/null
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null
    fi
    rm -f "$inst_dir/pid.txt"
    echo -e "  ${YELLOW}●${NC} $label 已停止"
}

# ============================================
# 前台首次登录（扫码）
# ============================================
first_login() {
    local buff=$1
    local slot=$2
    local inst_dir=$(get_instance_dir "$buff" "$slot")
    local label="$buff/$slot"

    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $label 不存在${NC}"
        return 1
    fi

    echo -e "${CYAN}============================================"
    echo "  首次登录: $label"
    echo -e "============================================${NC}"
    echo ""
    echo "请按照终端提示扫码登录 BUFF"
    echo "登录成功后按 Ctrl+C 退出即可"
    echo ""

    cd "$inst_dir"
    python3 Steamauto.py
}

# ============================================
# 命令: start <buff号/实例名>
# ============================================
cmd_start() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh start 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    start_instance "$BUFF_NUM" "$INSTANCE_NAME"
}

# ============================================
# 命令: start-buff <buff号>
# ============================================
cmd_start_buff() {
    local buff=$1
    local buff_dir="$ACCOUNTS_DIR/$buff"
    if [ ! -d "$buff_dir" ]; then
        echo -e "${RED}BUFF号 $buff 不存在${NC}"
        exit 1
    fi
    echo -e "${GREEN}正在启动 $buff 下所有实例...${NC}"
    for slot_dir in "$buff_dir"/steam_*/; do
        [ -d "$slot_dir" ] || continue
        local slot=$(basename "$slot_dir")
        start_instance "$buff" "$slot"
    done
}

# ============================================
# 命令: stop <buff号/实例名>
# ============================================
cmd_stop() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh stop 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    stop_instance "$BUFF_NUM" "$INSTANCE_NAME"
}

# ============================================
# 命令: stop-buff <buff号>
# ============================================
cmd_stop_buff() {
    local buff=$1
    local buff_dir="$ACCOUNTS_DIR/$buff"
    if [ ! -d "$buff_dir" ]; then
        echo -e "${RED}BUFF号 $buff 不存在${NC}"
        exit 1
    fi
    echo -e "${YELLOW}正在停止 $buff 下所有实例...${NC}"
    for slot_dir in "$buff_dir"/steam_*/; do
        [ -d "$slot_dir" ] || continue
        local slot=$(basename "$slot_dir")
        stop_instance "$buff" "$slot"
    done
}

# ============================================
# 命令: status
# ============================================
cmd_status() {
    echo -e "${CYAN}============================================"
    echo "  实例运行状态"
    echo -e "============================================${NC}"
    echo ""

    local total_running=0
    local total_stopped=0

    for buff_dir in "$ACCOUNTS_DIR"/*/; do
        [ -d "$buff_dir" ] || continue
        local buff=$(basename "$buff_dir")
        local buff_running=0
        local buff_total=0

        for slot_dir in "$buff_dir"/steam_*/; do
            [ -d "$slot_dir" ] || continue
            local slot=$(basename "$slot_dir")
            ((buff_total++))

            if [ -f "$slot_dir/pid.txt" ]; then
                local pid=$(cat "$slot_dir/pid.txt")
                if kill -0 "$pid" 2>/dev/null; then
                    ((buff_running++))
                    ((total_running++))
                    continue
                fi
            fi
            ((total_stopped++))
        done

        if [ $buff_running -eq $buff_total ] && [ $buff_total -gt 0 ]; then
            echo -e "  ${GREEN}●${NC} $buff  ${GREEN}$buff_running/$buff_total 运行中${NC}"
        elif [ $buff_running -gt 0 ]; then
            echo -e "  ${BLUE}◐${NC} $buff  ${BLUE}$buff_running/$buff_total 运行中${NC}"
        else
            echo -e "  ${RED}○${NC} $buff  ${RED}$buff_running/$buff_total 已停止${NC}"
        fi
    done

    echo ""
    echo -e "  总计: ${GREEN}$total_running 运行中${NC} / ${RED}$total_stopped 已停止${NC} / $((total_running + total_stopped)) 总实例"
}

# ============================================
# 命令: status-buff <buff号>
# ============================================
cmd_status_buff() {
    local buff=$1
    local buff_dir="$ACCOUNTS_DIR/$buff"
    if [ ! -d "$buff_dir" ]; then
        echo -e "${RED}BUFF号 $buff 不存在${NC}"
        exit 1
    fi

    echo -e "${CYAN}$buff 实例详情:${NC}"
    for slot_dir in "$buff_dir"/steam_*/; do
        [ -d "$slot_dir" ] || continue
        local slot=$(basename "$slot_dir")
        if [ -f "$slot_dir/pid.txt" ]; then
            local pid=$(cat "$slot_dir/pid.txt")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}●${NC} $slot  ${GREEN}运行中${NC} (PID: $pid)"
                continue
            fi
        fi
        echo -e "  ${RED}○${NC} $slot  ${RED}已停止${NC}"
    done
}

# ============================================
# 命令: start-all
# ============================================
cmd_start_all() {
    echo -e "${GREEN}正在启动所有实例...${NC}"
    for buff_dir in "$ACCOUNTS_DIR"/*/; do
        [ -d "$buff_dir" ] || continue
        local buff=$(basename "$buff_dir")
        for slot_dir in "$buff_dir"/steam_*/; do
            [ -d "$slot_dir" ] || continue
            local slot=$(basename "$slot_dir")
            start_instance "$buff" "$slot"
        done
    done
    echo ""
    echo -e "${GREEN}全部启动完成${NC}"
}

# ============================================
# 命令: stop-all
# ============================================
cmd_stop_all() {
    echo -e "${YELLOW}正在停止所有实例...${NC}"
    for buff_dir in "$ACCOUNTS_DIR"/*/; do
        [ -d "$buff_dir" ] || continue
        local buff=$(basename "$buff_dir")
        for slot_dir in "$buff_dir"/steam_*/; do
            [ -d "$slot_dir" ] || continue
            local slot=$(basename "$slot_dir")
            stop_instance "$buff" "$slot"
        done
    done
    echo ""
    echo -e "${GREEN}全部停止完成${NC}"
}

# ============================================
# 命令: config <buff号/实例名>
# ============================================
cmd_config() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh config 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    local inst_dir=$(get_instance_dir "$BUFF_NUM" "$INSTANCE_NAME")
    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $BUFF_NUM/$INSTANCE_NAME 不存在${NC}"
        exit 1
    fi
    vim "$inst_dir/config/steam_account_info.json5"
}

# ============================================
# 命令: log <buff号/实例名>
# ============================================
cmd_log() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh log 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    local inst_dir=$(get_instance_dir "$BUFF_NUM" "$INSTANCE_NAME")
    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $BUFF_NUM/$INSTANCE_NAME 不存在${NC}"
        exit 1
    fi

    local latest_log=$(ls -t "$inst_dir/logs/"*.log 2>/dev/null | head -1)
    if [ -z "$latest_log" ]; then
        echo -e "${YELLOW}暂无日志文件${NC}"
        return
    fi
    echo -e "${CYAN}$BUFF_NUM/$SLOT 日志:${NC}"
    tail -f "$latest_log"
}

# ============================================
# 命令: list
# ============================================
cmd_list() {
    echo -e "${CYAN}已配置的实例:${NC}"
    echo ""
    for buff_dir in "$ACCOUNTS_DIR"/*/; do
        [ -d "$buff_dir" ] || continue
        local buff=$(basename "$buff_dir")
        local count=$(ls -d "$buff_dir"/steam_*/ 2>/dev/null | wc -l | tr -d ' ')
        echo -e "  ${BLUE}$buff${NC} ($count 个Steam槽位)"
        for slot_dir in "$buff_dir"/steam_*/; do
            [ -d "$slot_dir" ] || continue
            local slot=$(basename "$slot_dir")
            echo "    └─ $slot"
        done
    done
    echo ""
    local total=$(find "$ACCOUNTS_DIR" -name "steam_*" -type d 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  总实例数: $total"
}

# ============================================
# 命令: first-login <buff号/实例名>
# ============================================
cmd_first_login() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh first-login 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    first_login "$BUFF_NUM" "$INSTANCE_NAME"
}

# ============================================
# 命令: first-login-buff <buff号>
# ============================================
cmd_first_login_buff() {
    local buff=$1
    local buff_dir="$ACCOUNTS_DIR/$buff"
    if [ ! -d "$buff_dir" ]; then
        echo -e "${RED}BUFF号 $buff 不存在${NC}"
        exit 1
    fi
    echo -e "${CYAN}将依次前台登录 $buff 下所有实例${NC}"
    echo "每个实例扫码成功后按 Ctrl+C，然后自动进入下一个"
    echo ""

    for slot_dir in "$buff_dir"/steam_*/; do
        [ -d "$slot_dir" ] || continue
        local slot=$(basename "$slot_dir")
        first_login "$buff" "$slot"
        echo ""
        echo -e "${GREEN}--- $slot 完成，5秒后继续下一个 ---${NC}"
        sleep 5
    done
    echo -e "${GREEN}全部首次登录完成！${NC}"
}

# ============================================
# 主逻辑
# ============================================
case "${1:-}" in
    start)
        cmd_start "$2"
        ;;
    start-buff)
        cmd_start_buff "$2"
        ;;
    start-all)
        cmd_start_all
        ;;
    stop)
        cmd_stop "$2"
        ;;
    stop-buff)
        cmd_stop_buff "$2"
        ;;
    stop-all)
        cmd_stop_all
        ;;
    status)
        cmd_status
        ;;
    status-buff)
        cmd_status_buff "$2"
        ;;
    config)
        cmd_config "$2"
        ;;
    log)
        cmd_log "$2"
        ;;
    list)
        cmd_list
        ;;
    first-login)
        cmd_first_login "$2"
        ;;
    first-login-buff)
        cmd_first_login_buff "$2"
        ;;
    *)
        show_help
        ;;
esac
```

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
程序版本: 3.18
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

| BUFF号 | 类型 | 实例数 | 实例目录（{steam_username}_{steam_id}） |
|--------|------|--------|---------|
| 17328515660 | 会员 | 10 | 待重命名（当前为 steam_01 ~ steam_10） |
| 13510278160 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 17324473850 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 13242040227 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 13265677880 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 15362053264 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 15813347556 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 17724562830 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 17818370030 | 普通 | 1 | 待重命名（当前为 steam_01） |
| 17827629720 | 普通 | 1 | 待重命名（当前为 steam_01） |

**总计：19 个实例**

---

## 七、关键说明

### 源码共享（已改造 ✅）
所有 19 个实例通过**符号链接**共享 `Steamauto/` 目录下的源码。更新源码只需：

```bash
./manage.sh stop-all          # 停止全部
cd Steamauto && git pull       # 拉取最新源码（所有实例自动生效）
pip3 install -r requirements.txt  # 安装新依赖（如有）
./manage.sh start-all          # 重新启动
```

或直接使用 `./manage.sh update` 一键完成上述步骤。

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

## 八、源码更新策略

### 8.1 当前方案的问题

当前每个实例目录都有一份完整的源码拷贝（`Steamauto.py`、`utils/`、`steampy/` 等），共 19 份副本。这意味着：

- **更新繁琐**：上游更新后需要逐个实例覆盖源码
- **磁盘浪费**：19 份源码副本占用大量空间
- **版本不一致风险**：可能漏更新某些实例

### 8.2 推荐方案：符号链接共享源码

Steamauto 的关键设计：**所有路径（config/、session/、logs/）都是相对路径**，基于当前工作目录。因此可以让所有实例共享同一份源码，每个实例只保留自己的用户数据。

**改造后的目录结构：**

```
├── Steamauto/                 # 唯一源码，git pull 即可更新所有实例
│   ├── Steamauto.py
│   ├── utils/
│   ├── steampy/
│   ├── BuffApi/
│   ├── plugins/
│   └── ...
├── accounts/
│   └── 17827629720/azc23232_76561199268318177/
│       ├── Steamauto.py  -> ../../../Steamauto/Steamauto.py   (符号链接)
│       ├── utils/        -> ../../../Steamauto/utils/
│       ├── steampy/      -> ../../../Steamauto/steampy/
│       ├── BuffApi/      -> ../../../Steamauto/BuffApi/
│       ├── plugins/      -> ../../../Steamauto/plugins/
│       ├── ...           (所有源码目录都是符号链接)
│       ├── config/       # 【独立】用户数据
│       ├── session/      # 【独立】Steam 会话
│       └── logs/         # 【独立】运行日志
└── manage.sh
```

### 8.3 一次性改造脚本

将以下内容保存为 `migrate_to_symlink.sh`，在项目根目录运行：

```bash
#!/bin/bash
# 将当前所有实例的源码目录替换为指向 Steamauto/ 的符号链接
# 运行前请先 ./manage.sh stop-all 停止所有实例

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/Steamauto"
ACCOUNTS="$SCRIPT_DIR/accounts"

# 需要链接的源码目录/文件列表
SYMLINK_TARGETS=(
    "Steamauto.py"
    "BuffApi"
    "plugins"
    "protobufs"
    "PyC5Game"
    "PyECOsteam"
    "steampy"
    "utils"
    "uuyoupinapi"
)

echo "将改造所有实例，源码目录替换为符号链接..."
echo ""

for buff_dir in "$ACCOUNTS"/*/; do
    [ -d "$buff_dir" ] || continue
    buff=$(basename "$buff_dir")
    
    for slot_dir in "$buff_dir"/steam_*/; do
        [ -d "$slot_dir" ] || continue
        slot=$(basename "$slot_dir")
        echo -n "  $buff/$slot ... "
        
        cd "$slot_dir"
        
        for target in "${SYMLINK_TARGETS[@]}"; do
            # 计算相对路径
            REL_PATH=$(python3 -c "import os; print(os.path.relpath('$SRC/$target', '$slot_dir'))")
            
            # 如果已经是符号链接，跳过
            if [ -L "$target" ]; then
                continue
            fi
            
            # 如果是目录或文件，删除后创建符号链接
            if [ -e "$target" ]; then
                rm -rf "$target"
            fi
            ln -s "$REL_PATH" "$target"
        done
        
        echo "✓"
    done
done

echo ""
echo "改造完成！现在所有实例共享 Steamauto/ 目录的源码。"
echo "更新源码只需: cd Steamauto && git pull"
```

### 8.4 改造后的更新流程

```bash
# 1. 停止所有实例
./manage.sh stop-all

# 2. 拉取最新源码（所有实例自动生效）
cd Steamauto
git pull
cd ..

# 3. 如果有新的 Python 依赖
pip3 install -r Steamauto/requirements.txt

# 4. 重新启动
./manage.sh start-all
```

**一步到位，19 个实例全部更新完毕。**

### 8.5 改造后新增实例

```bash
# 新增实例时，只需创建目录 + 符号链接 + 配置文件
BUFF_NUM="新BUFF号"
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

# 写入配置文件（根据模板修改）
cp Steamauto/config/config.json5 "$INST_DIR/config/"
cp Steamauto/config/steam_account_info.json5 "$INST_DIR/config/"
# 编辑 $INST_DIR/config/config.json5（代理设置）
# 编辑 $INST_DIR/config/steam_account_info.json5（Steam信息）

# 首次登录 + 启动
./manage.sh first-login "$BUFF_NUM/$SLOT"
./manage.sh start "$BUFF_NUM/$SLOT"
```

### 8.6 注意事项

| 目录/文件 | 类型 | 说明 |
|-----------|------|------|
| `config/` | 独立数据 | 每个实例的配置、Cookie、令牌，**不可共享** |
| `session/` | 独立数据 | Steam 登录会话，**不可共享** |
| `logs/` | 独立数据 | 运行日志，**不可共享** |
| `nohup.log` | 独立数据 | 后台运行日志 |
| `pid.txt` | 独立数据 | 进程 PID |
| `Steamauto.py` | 符号链接 → 源码 | 主入口 |
| `utils/` | 符号链接 → 源码 | 工具模块 |
| `steampy/` | 符号链接 → 源码 | Steam 客户端 |
| `BuffApi/` | 符号链接 → 源码 | BUFF API |
| `plugins/` | 符号链接 → 源码 | 插件目录 |
| 其他源码目录 | 符号链接 → 源码 | 共享代码 |

> **核心原则**：凡是 Steamauto 项目自带的文件/目录都做成符号链接，凡是运行时产生的用户数据都保留为真实目录。

### 8.7 批量写入 steam_account_info.json5

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
cat accounts/17827629720/azc23232_76561199268318177/nohup.log

# 查看 Steamauto 运行日志
tail -f accounts/17827629720/azc23232_76561199268318177/logs/*.log

# 手动杀掉残留进程
kill $(cat accounts/17827629720/azc23232_76561199268318177/pid.txt)

# 清理所有 PID 文件（如果状态显示异常）
find accounts -name "pid.txt" -delete

# 检查符号链接是否完好
find accounts -type l -exec test ! -e {} \; -print

# 修复断开的符号链接（如果 Steamauto 目录移动了）
# 重新运行 migrate_to_symlink.sh 即可
```
