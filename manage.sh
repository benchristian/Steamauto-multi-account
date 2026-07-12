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
    echo "  check-login            检查所有实例登录状态（是否登录失效）"
    echo "  config <buff号/实例名> 编辑指定实例的Steam配置"
    echo "  log <buff号/实例名>    实时查看指定实例日志"
    echo "  list                   列出所有实例"
    echo "  first-login <buff号/实例名> 前台运行以完成首次扫码登录"
    echo "  first-login-buff <buff号> 依次前台登录某BUFF号所有实例"
    echo "  rename <buff号/实例名> 按 {steam_username}_{steam_id} 格式重命名实例目录"
    echo "  rename-buff <buff号>   重命名某BUFF号下所有实例目录"
    echo "  rename-all             重命名所有实例目录"
    echo "  update                 拉取Steamauto最新源码并重启所有实例"
    echo "  update-check           仅检查Steamauto是否有更新"
    echo "  stats <buff号/实例名>  统计指定实例的出售记录(调用BUFF API)"
    echo "  stats-buff <buff号>    统计某BUFF号下所有实例的出售记录"
    echo "  stats-all              统计所有实例的出售记录"
    echo "  stats-list             列出所有实例及其统计文件"
    echo "  import-mafile          从 steam-desktop-authenticator 导入 maFile 配置到 steam_account_info.json5"
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
    local name=$2
    echo "$ACCOUNTS_DIR/$buff/$name"
}

# 列出某BUFF号下所有实例目录（排除隐藏目录和非目录文件）
list_instance_dirs() {
    local buff_dir=$1
    for d in "$buff_dir"/*/; do
        [ -d "$d" ] || continue
        local name=$(basename "$d")
        # 排除隐藏目录
        [[ "$name" == .* ]] && continue
        echo "$d"
    done
}

# 列出所有BUFF号目录
list_buff_dirs() {
    for d in "$ACCOUNTS_DIR"/*/; do
        [ -d "$d" ] || continue
        local name=$(basename "$d")
        [[ "$name" == .* ]] && continue
        echo "$d"
    done
}

# ============================================
# 启动单个实例
# ============================================
start_instance() {
    local buff=$1
    local name=$2
    local inst_dir=$(get_instance_dir "$buff" "$name")
    local label="$buff/$name"

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
    local name=$2
    local inst_dir=$(get_instance_dir "$buff" "$name")
    local label="$buff/$name"

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
    local name=$2
    local inst_dir=$(get_instance_dir "$buff" "$name")
    local label="$buff/$name"

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
    while IFS= read -r slot_dir; do
        local name=$(basename "$slot_dir")
        start_instance "$buff" "$name"
    done < <(list_instance_dirs "$buff_dir")
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
    while IFS= read -r slot_dir; do
        local name=$(basename "$slot_dir")
        stop_instance "$buff" "$name"
    done < <(list_instance_dirs "$buff_dir")
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

    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")
        local buff_running=0
        local buff_total=0

        while IFS= read -r slot_dir; do
            local name=$(basename "$slot_dir")
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
        done < <(list_instance_dirs "$buff_dir")

        if [ $buff_running -eq $buff_total ] && [ $buff_total -gt 0 ]; then
            echo -e "  ${GREEN}●${NC} $buff  ${GREEN}$buff_running/$buff_total 运行中${NC}"
        elif [ $buff_running -gt 0 ]; then
            echo -e "  ${BLUE}◐${NC} $buff  ${BLUE}$buff_running/$buff_total 运行中${NC}"
        else
            echo -e "  ${RED}○${NC} $buff  ${RED}$buff_running/$buff_total 已停止${NC}"
        fi
    done < <(list_buff_dirs)

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
    while IFS= read -r slot_dir; do
        local name=$(basename "$slot_dir")
        if [ -f "$slot_dir/pid.txt" ]; then
            local pid=$(cat "$slot_dir/pid.txt")
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}●${NC} $name  ${GREEN}运行中${NC} (PID: $pid)"
                continue
            fi
        fi
        echo -e "  ${RED}○${NC} $name  ${RED}已停止${NC}"
    done < <(list_instance_dirs "$buff_dir")
}

# ============================================
# 命令: check-login - 检查所有实例登录状态
# ============================================
cmd_check_login() {
    echo -e "${CYAN}============================================"
    echo "  实例登录状态检查"
    echo -e "============================================${NC}"
    echo ""

    local ok=0 warn=0 err=0

    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")

        while IFS= read -r slot_dir; do
            local name=$(basename "$slot_dir")
            local label="${buff}/${name}"
            local logs_dir="$slot_dir/logs"

            # 1. 进程状态
            local proc_alive="无PID"
            if [ -f "$slot_dir/pid.txt" ]; then
                local pid=$(cat "$slot_dir/pid.txt")
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    proc_alive="存活"
                else
                    proc_alive="已死"
                fi
            fi

            # 2. 最新日志分析
            local last_ts="无日志"
            local login_status=""
            local has_buff=false

            if [ -d "$logs_dir" ]; then
                local latest_log=$(ls -t "$logs_dir"/*.log 2>/dev/null | head -1)
                if [ -n "$latest_log" ]; then
                    # 最后一条时间戳
                    last_ts=$(tail -20 "$latest_log" | grep -o '\[20[0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]\]' | tail -1)
                    [ -z "$last_ts" ] && last_ts="无时间戳"

                    # 是否有 BUFF 业务日志
                    if grep -q "BuffAutoAcceptOffer\|buff.163.com" "$latest_log" 2>/dev/null; then
                        has_buff=true
                    fi

                    # 登录状态检测（优先级从高到低）
                    if grep -q "登录成功\|Steam登录成功\|login success" "$latest_log" 2>/dev/null; then
                        login_status="已登录"
                    elif grep -q "密码错误\|password.*错误" "$latest_log" 2>/dev/null; then
                        login_status="密码错误"
                    elif grep -q "令牌.*错误\|令牌.*无效\|shared_secret.*错误" "$latest_log" 2>/dev/null; then
                        login_status="令牌错误"
                    elif grep -q "请扫码\|扫码登录\|QR.*code" "$latest_log" 2>/dev/null; then
                        login_status="需扫码"
                    elif grep -q "Cookie.*过期\|cookie.*expired\|会话.*过期" "$latest_log" 2>/dev/null; then
                        login_status="Cookie过期"
                    elif grep -q "登录失败\|login.*fail\|Steam登录失败" "$latest_log" 2>/dev/null; then
                        login_status="登录失败"
                    elif grep -q "连接超时\|Connection.*timed\|网络异常" "$latest_log" 2>/dev/null; then
                        login_status="网络异常"
                    elif grep -q "EOFError\|致命错误" "$latest_log" 2>/dev/null; then
                        login_status="程序异常退出"
                    fi
                fi
            fi

            # 3. 综合判断
            local state state_color
            if [ "$proc_alive" = "存活" ] && [ "$has_buff" = true ] && [ "$login_status" = "已登录" ]; then
                state="✅ 正常"
                state_color="$GREEN"
                ((ok++))
            elif [ "$proc_alive" = "存活" ] && [ "$has_buff" = false ]; then
                state="⚠️ 空转"
                state_color="$YELLOW"
                if [ -n "$login_status" ]; then
                    state="$state ($login_status)"
                fi
                ((warn++))
            elif [ "$proc_alive" = "已死" ] || [ "$proc_alive" = "无PID" ]; then
                state="❌ 已停止"
                state_color="$RED"
                ((err++))
            elif [ -n "$login_status" ]; then
                state="❌ $login_status"
                state_color="$RED"
                ((err++))
            else
                state="❓ 状态不明"
                state_color="$YELLOW"
                ((warn++))
            fi

            printf "  ${state_color}%-45s${NC} | %s | %s\n" "$state" "$label" "$last_ts"

        done < <(list_instance_dirs "$buff_dir")
    done < <(list_buff_dirs)

    echo ""
    echo -e "  总计: ${GREEN}$ok 正常${NC} / ${YELLOW}$warn 警告${NC} / ${RED}$err 异常${NC}"
    echo ""
    if [ $err -gt 0 ]; then
        echo -e "  ${RED}⚠ 有 $err 个实例需要处理！${NC}"
        echo -e "  可尝试: ./manage.sh first-login <实例名> 重新扫码登录"
    fi
}

# ============================================
# 命令: start-all
# ============================================
cmd_start_all() {
    echo -e "${GREEN}正在启动所有实例...${NC}"
    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")
        while IFS= read -r slot_dir; do
            local name=$(basename "$slot_dir")
            start_instance "$buff" "$name"
        done < <(list_instance_dirs "$buff_dir")
    done < <(list_buff_dirs)
    echo ""
    echo -e "${GREEN}全部启动完成${NC}"
}

# ============================================
# 命令: stop-all
# ============================================
cmd_stop_all() {
    echo -e "${YELLOW}正在停止所有实例...${NC}"
    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")
        while IFS= read -r slot_dir; do
            local name=$(basename "$slot_dir")
            stop_instance "$buff" "$name"
        done < <(list_instance_dirs "$buff_dir")
    done < <(list_buff_dirs)
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
    echo -e "${CYAN}$BUFF_NUM/$INSTANCE_NAME 日志:${NC}"
    tail -f "$latest_log"
}

# ============================================
# 命令: list
# ============================================
cmd_list() {
    echo -e "${CYAN}已配置的实例:${NC}"
    echo ""
    local total=0
    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")
        local count=0
        while IFS= read -r slot_dir; do
            ((count++))
            ((total++))
            local name=$(basename "$slot_dir")
            if [ $count -eq 1 ]; then
                echo -e "  ${BLUE}$buff${NC} ($count 个实例)"
            fi
            echo "    └─ $name"
        done < <(list_instance_dirs "$buff_dir")
        if [ $count -gt 1 ]; then
            # 修正第一行的计数显示
            echo -ne "\033[1A\033[2K\r"
            echo -e "  ${BLUE}$buff${NC} ($count 个实例)"
        fi
    done < <(list_buff_dirs)
    echo ""
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

    while IFS= read -r slot_dir; do
        local name=$(basename "$slot_dir")
        first_login "$buff" "$name"
        echo ""
        echo -e "${GREEN}--- $name 完成，5秒后继续下一个 ---${NC}"
        sleep 5
    done < <(list_instance_dirs "$buff_dir")
    echo -e "${GREEN}全部首次登录完成！${NC}"
}

# ============================================
# 命令: update-check
# ============================================
cmd_update_check() {
    echo -e "${CYAN}检查 Steamauto 源码更新...${NC}"
    cd "$STEAMAUTO_DIR"

    local current=$(git rev-parse --short HEAD 2>/dev/null)
    if [ -z "$current" ]; then
        echo -e "${RED}Steamauto 目录不是 git 仓库${NC}"
        exit 1
    fi

    git fetch origin 2>/dev/null
    local remote=$(git rev-parse --short origin/master 2>/dev/null)
    local behind=$(git rev-list --count HEAD..origin/master 2>/dev/null)

    echo "  当前版本: $current"
    echo "  远程版本: $remote"

    if [ "$current" = "$remote" ]; then
        echo -e "  ${GREEN}已是最新版本${NC}"
    else
        echo -e "  ${YELLOW}有 $behind 个新提交可更新${NC}"
    fi
}

# ============================================
# 命令: update
# ============================================
cmd_update() {
    echo -e "${CYAN}============================================"
    echo "  Steamauto 源码更新"
    echo -e "============================================${NC}"
    echo ""

    # 1. 检查是否有实例在运行
    local running=0
    while IFS= read -r buff_dir; do
        while IFS= read -r slot_dir; do
            if [ -f "$slot_dir/pid.txt" ]; then
                local pid=$(cat "$slot_dir/pid.txt")
                if kill -0 "$pid" 2>/dev/null; then
                    ((running++))
                fi
            fi
        done < <(list_instance_dirs "$buff_dir")
    done < <(list_buff_dirs)

    if [ $running -gt 0 ]; then
        echo -e "${YELLOW}检测到 $running 个实例正在运行，将自动停止...${NC}"
        cmd_stop_all
        sleep 2
    fi

    # 2. 拉取最新源码
    echo -e "${GREEN}拉取 Steamauto 最新源码...${NC}"
    cd "$STEAMAUTO_DIR"
    local before=$(git rev-parse --short HEAD)
    git pull
    local after=$(git rev-parse --short HEAD)
    cd "$SCRIPT_DIR"

    if [ "$before" = "$after" ]; then
        echo -e "${GREEN}已是最新版本，无需更新${NC}"
    else
        echo -e "${GREEN}更新成功: $before -> $after${NC}"

        # 3. 检查是否有新依赖
        if [ -f "$STEAMAUTO_DIR/requirements.txt" ]; then
            echo ""
            echo -e "${YELLOW}检查 Python 依赖更新...${NC}"
            pip3 install -r "$STEAMAUTO_DIR/requirements.txt" 2>&1 | tail -3
        fi
    fi

    # 4. 如果之前有实例在运行，询问是否重启
    if [ $running -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}更新前有 $running 个实例在运行，是否重新启动？(y/n)${NC}"
        read -r answer
        if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
            cmd_start_all
        fi
    fi

    echo ""
    echo -e "${GREEN}更新完成！${NC}"
}

# ============================================
# 命令: stats <buff号/实例名>
# ============================================
cmd_stats() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh stats 17827629720/azc23232_76561199268318177${NC}"
        exit 1
    fi
    local inst_dir="$ACCOUNTS_DIR/$BUFF_NUM/$INSTANCE_NAME"
    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例目录不存在: $BUFF_NUM/$INSTANCE_NAME${NC}"
        exit 1
    fi
    python3 "$SCRIPT_DIR/stats.py" "$inst_dir"
}

# ============================================
# 命令: stats-buff <buff号>
# ============================================
cmd_stats_buff() {
    if [ -z "$1" ]; then
        echo -e "${RED}请指定BUFF号，例如: ./manage.sh stats-buff 17328515660${NC}"
        exit 1
    fi
    python3 "$SCRIPT_DIR/stats.py" --buff "$1"
}

# ============================================
# 命令: stats-all
# ============================================
cmd_stats_all() {
    python3 "$SCRIPT_DIR/stats.py" --all
}

# ============================================
# 命令: stats-list
# ============================================
cmd_stats_list() {
    python3 "$SCRIPT_DIR/stats.py" --list
}

# ============================================
# 命令: rename <buff号/实例名>  — 将目录重命名为 {steam_username}_{steam_id}
# ============================================
rename_instance() {
    local buff=$1
    local name=$2
    local inst_dir=$(get_instance_dir "$buff" "$name")
    local label="$buff/$name"

    if [ ! -d "$inst_dir" ]; then
        echo -e "${RED}实例 $label 不存在${NC}"
        return 1
    fi

    # 读取 steam_account_info.json5 获取 steam_username
    local info_file="$inst_dir/config/steam_account_info.json5"
    if [ ! -f "$info_file" ]; then
        echo -e "${RED}$label 没有 steam_account_info.json5 配置文件${NC}"
        return 1
    fi

    # 简易解析 JSON5 获取 steam_username（去除注释后用 python3 解析）
    local steam_username=$(python3 -c "
import json, re, sys
try:
    with open('$info_file', 'r') as f:
        text = f.read()
    text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    cfg = json.loads(text)
    print(cfg.get('steam_username', ''))
except:
    print('')
" 2>/dev/null)

    if [ -z "$steam_username" ]; then
        echo -e "${RED}$label: steam_username 未配置，无法重命名${NC}"
        return 1
    fi

    # 尝试获取 steam_id（从 session 目录或 buff_cookies 文件名提取）
    local steam_id=""
    # 方式1: 从 session 目录的 json 文件
    local session_dir="$inst_dir/session"
    if [ -d "$session_dir" ]; then
        steam_id=$(python3 -c "
import json, os
session_dir = '$session_dir'
try:
    for f in os.listdir(session_dir):
        if f.endswith('.json'):
            with open(os.path.join(session_dir, f)) as fh:
                data = json.load(fh)
                if 'steamid' in data:
                    print(data['steamid'])
                    break
except:
    pass
" 2>/dev/null)
    fi

    # 方式2: 从 buff_cookies 文件名提取
    if [ -z "$steam_id" ]; then
        local config_dir="$inst_dir/config"
        if [ -d "$config_dir" ]; then
            for f in "$config_dir"/buff_cookies_*.txt; do
                [ -f "$f" ] || continue
                local fname=$(basename "$f")
                # 格式: buff_cookies_{steam_username}.txt — 尝试从 cookie 内容中提取 steamLoginSecure
                local cookie_steamid=$(grep -o 'steamLoginSecure=[^;]*' "$f" 2>/dev/null | cut -d= -f2 | cut -d'%' -f1)
                if [ -n "$cookie_steamid" ]; then
                    steam_id="$cookie_steamid"
                    break
                fi
            done
        fi
    fi

    # 如果无法获取 steam_id，使用当前目录名作为后备
    if [ -z "$steam_id" ]; then
        steam_id="$name"
        echo -e "${YELLOW}  无法获取 steam_id，将使用当前目录名作为标识${NC}"
    fi

    local new_name="${steam_username}_${steam_id}"
    local new_dir="$ACCOUNTS_DIR/$buff/$new_name"

    if [ "$name" = "$new_name" ]; then
        echo -e "${GREEN}$label 已是目标格式，无需重命名${NC}"
        return 0
    fi

    if [ -d "$new_dir" ]; then
        echo -e "${RED}目标目录已存在: $buff/$new_name${NC}"
        return 1
    fi

    mv "$inst_dir" "$new_dir"
    echo -e "${GREEN}✓ $label → $buff/$new_name${NC}"
    return 0
}

cmd_rename() {
    parse_target "$1"
    if [ -z "$INSTANCE_NAME" ]; then
        echo -e "${RED}请指定完整路径，例如: ./manage.sh rename 17827629720/steam_01${NC}"
        exit 1
    fi
    rename_instance "$BUFF_NUM" "$INSTANCE_NAME"
}

cmd_rename_buff() {
    local buff=$1
    local buff_dir="$ACCOUNTS_DIR/$buff"
    if [ ! -d "$buff_dir" ]; then
        echo -e "${RED}BUFF号 $buff 不存在${NC}"
        exit 1
    fi
    echo -e "${CYAN}正在重命名 $buff 下所有实例...${NC}"
    while IFS= read -r slot_dir; do
        local name=$(basename "$slot_dir")
        rename_instance "$buff" "$name"
    done < <(list_instance_dirs "$buff_dir")
    echo ""
    echo -e "${GREEN}重命名完成！${NC}"
}

cmd_rename_all() {
    echo -e "${CYAN}正在重命名所有实例...${NC}"
    echo ""
    while IFS= read -r buff_dir; do
        local buff=$(basename "$buff_dir")
        while IFS= read -r slot_dir; do
            local name=$(basename "$slot_dir")
            rename_instance "$buff" "$name"
        done < <(list_instance_dirs "$buff_dir")
    done < <(list_buff_dirs)
    echo ""
    echo -e "${GREEN}全部重命名完成！${NC}"
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
    check-login)
        cmd_check_login
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
    update)
        cmd_update
        ;;
    update-check)
        cmd_update_check
        ;;
    stats)
        cmd_stats "$2"
        ;;
    stats-buff)
        cmd_stats_buff "$2"
        ;;
    stats-all)
        cmd_stats_all
        ;;
    stats-list)
        cmd_stats_list
        ;;
    import-mafile)
        python3 "$SCRIPT_DIR/import_mafile.py" "${@:2}"
        ;;
    rename)
        cmd_rename "$2"
        ;;
    rename-buff)
        cmd_rename_buff "$2"
        ;;
    rename-all)
        cmd_rename_all
        ;;
    *)
        show_help
        ;;
esac
