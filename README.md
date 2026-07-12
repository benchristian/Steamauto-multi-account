# Steamauto 多账号管理工具集

基于 [Steamauto](https://github.com/Steamauto/Steamauto) 的 BUFF 自动发货多账号管理方案，支持一台机器同时运行 20+ Steam 账号的自动出售发货。

## 快速开始

```bash
git clone --recursive https://github.com/benchristian/Steamauto-multi-account.git
cd Steamauto-multi-account
```

### 常用命令

```bash
./manage.sh start-all    # 启动所有实例
./manage.sh status       # 查看运行状态
./manage.sh stop-all     # 停止所有实例
./manage.sh update       # 更新 Steamauto 源码并重启
./manage.sh stats-all    # 同步所有账号出售记录
```

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `manage.sh` | 多实例管理（启停、状态、日志、更新、统计等） |
| `stats.py` | 通过 BUFF API 同步出售记录，生成统计报告 |
| `import_mafile.py` | 从 maFile 目录导入令牌密钥到实例配置 |
| `write_account_info.py` | 从 CSV + maFile 批量生成实例配置 |
| `set_passwords.py` | 从 CSV 批量写入 Steam 密码 |

> 完整说明见 [Steamauto多账号管理方案.md](./Steamauto多账号管理方案.md)

## 项目结构

```
├── manage.sh                          # 多实例管理脚本
├── stats.py / import_mafile.py / ...  # 辅助脚本
├── Steamauto/                         # [submodule] Steamauto 主项目
├── Steamauto多账号管理方案.md          # 完整方案文档
└── accounts/                          # 账号数据（不纳入版本控制）
    └── <BUFF号>/
        └── <steam_username>_<steam_id>/
```

## Steamauto Submodule

```bash
cd Steamauto && git pull origin master   # 直接更新
./manage.sh update                        # 或通过 manage.sh 一键更新
```

## 许可

本项目为 Steamauto 的配套管理工具集，遵循与原项目相同的许可协议。
