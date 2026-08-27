# 渔力全开 (How to Fish) - 内存修改器

[English](README.md) | [简体中文](README_zh.md)

专为 Unity Mono 引擎游戏 **[渔力全开 (How to Fish)](https://store.steampowered.com/)** 打造的外部内存修改器与辅助工具。

基于 `pymem` 与底层 Mono Runtime C API 互操作实现 JIT 函数 Hook / 机器码补丁，并提供 `rich` 现代化交互式终端控制面板，支持中英文双语无缝切换与免 Python 单文件 `.exe` 运行。

> **v0.2.0 RC：** 物品生成器已经通过自动化测试，但正式发布 v0.2.0 前仍需要在当前 Steam 版本中完成真实游戏验证。

---

## 功能特性

| 快捷键 | 功能名称 | 详细说明 |
| :--- | :--- | :--- |
| **F1** | **锁定生命** | 免疫所有外来伤害（NPC攻击、拳头、陷阱、火焰、中毒、饥饿），消除负面属性槽。**保留正常跳跃与物理受击反馈。** |
| **F2** | **锁定饱食度** | 阻止饱食度随时间自然流逝或因行为动作消耗，永久维持满腹状态。 |
| **F3** | **无限空中跳** | 纯跳跃逻辑补丁：允许在空中无限次连跳与凌空飞行（**不启用 InGodMode，不影响血量逻辑**）。 |
| **F4** | **无限弹药** | 所有枪械无限备弹与弹匣容量，射击不消耗子弹，无需频繁换弹。 |
| **F5** | **伤害倍率** | 循环切换枪械、近战武器与徒手拳头的伤害倍率：**`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `一击必杀 (99999)`**。 |
| **F6** | **增加金币 (+1w)** | 每次按下立即增加 **+$10,000 (1万)** 金币，附带金币音效、飘字动画与 HUD 数字滚动效果，并同步至联机网络。 |
| **F7** | **选择生成物品** | 打开响应式“ID / 物品”目录：大窗口每行四组并按高度增加每页数量，窄窗口自动减少栏数；红色 `!` 表示需要二次确认。 |
| **F8** | **生成当前物品** | 在相机前方约 2 米生成一个当前物品，仅支持单人游戏或房主。 |
| **F12** | **切换语言** | 随时在中英文界面之间切换：**中文 (ZH)** 与 **English (EN)**。 |
| **F10 / ESC** | **安全退出** | 自动还原所有已修改的机器码指令与内存基准值，无残留安全退出。 |

---

## 核心架构与实现原理

1. **Mono Runtime 互操作 (`howtofish_cheat.mono.bridge`)**：
   - 动态解析 `How to Fish.exe` 进程内 `mono-2.0-bdwgc.dll` 导出的 C API。
   - 创建远程线程附着至 Mono 根域（Root Domain）并配置 TLS 上下文。
   - 动态检索已加载程序集（`Assembly-CSharp`）、类元数据、方法指针及静态虚函数表（VTable）。

2. **JIT 编译与内存动态缩放 (`howtofish_cheat.mono.patcher`)**：
   - **锁定生命 (`F1`)**：JIT-Patch 拦截 `PlayerVitals.TakeDamage`、`PlayerVitals.LocalHit`、`PlayerVitals.DamageFromFullness`、`PlayerVitals.ApplyNewFire` 与 `PlayerVitals.ApplyNewPoison`。
   - **锁定饱食度 (`F2`)**：JIT-Patch 拦截 `PlayerVitals.LowerFullness` 与 `PlayerVitals.LowerFullnessTick`。
   - **无限空中跳 (`F3`)**：在 `PlayerMovement.JumpInput` 安装直接跳转至 `PlayerMovement.Jump` 的调用蹦床（Trampoline），实现空中无限多段跳。
   - **无限弹药 (`F4`)**：对 `Weapon.set_Ammo` 写入 `RET` (`0xC3`) 指令，并在内存中锁定弹匣容量为 `999` 及重置换弹标记。
   - **伤害倍率 (`F5`)**：实时动态缩放 `PlayerPunching._damage`、`Melee._sharpnessUpgrades` 数组、`Attachments._bulletUpgrades` 数组以及 `WeaponInfo.ProjectileDamage`（1x, 2x, 5x, 10x, 99999x）。
   - **增加金币 (`F6`)**：直接写入权威静态字段 `<Money>k__BackingField` 与 FishNet `SyncVar<int> _money`，触发 `PlayerUI.SetMoney` 播放飘字动画，并调用 `MoneyManager.MoneySound` 播放拾取音效。
   - **物品生成器 (`F7` / `F8`)**：精确解析 `GameInfo.GetSpawnable(byte)` 重载后枚举、分类物品，并通过一次性的 `Player.LateUpdate` 主线程入口调用 `DazedCommands.UseSpawnCommand`；每个命令字符串在一次游戏进程中只固定并缓存一次，不再调用已确认会崩溃的运行时 handle 释放；双向恢复握手让 Unity 线程停留在安全代码区，直到原方法入口完全恢复。普通联机客户端会被拒绝。
   - **安全还原**：关闭功能或退出修改器时，自动恢复原始机器码字节与伤害基准值。

3. **现代化终端 UI (`howtofish_cheat.ui.console`)**：
   - 基于 `rich` 构建的高刷新率仪表盘，实时展示游戏连接状态、进程 PID、Mono 域指针与各项功能开关。

---

## 使用指南

### 1. 获取并运行修改器

#### 方式 A：直接下载预编译独立可执行程序（推荐）
从 **[GitHub Releases](https://github.com/fredwangwang/how-to-fish-trainer/releases)** 下载最新的 `HowToFishTrainer.exe` 单文件版本，双击即可运行（无需安装 Python 或任何依赖环境）。

#### 方式 B：从源码运行（基于 uv）
```powershell
# 使用 uv 快速启动修改器
uv run python run_trainer.py

# 或者作为模块启动
uv run python -m howtofish_cheat

# 编译为单文件 exe 程序 (生成在 dist/HowToFishTrainer.exe)
uv run python build.py

# 运行自动化单元测试
uv run pytest -v
```

### 2. 游戏内热键操作
- 按 **F1** 开关 **锁定生命**
- 按 **F2** 开关 **锁定饱食度**
- 按 **F3** 开关 **无限空中跳跃**
- 按 **F4** 开关 **无限弹药**
- 按 **F5** 循环切换 **伤害倍率** (`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `一击必杀`)
- 按 **F6** 立即 **增加金币 (+1w / +$10,000)**
- 按 **F7** 打开物品目录，输入 ID 并确认当前物品
- 按 **F8** 在单人游戏或房主模式中生成一个当前物品
- 按 **F12** 随时 **切换语言 (中文 / English)**
- 按 **F10** / **ESC** / **Ctrl+C** 安全退出修改器

### 3. 物品生成器测试与诊断

首次测试请使用新建的临时存档。先在单人模式分别验证一条鱼和一把枪，再用第二个客户端验证房主生成后的可见性与拾取同步。任务或未知物品虽然会显示，但因可能影响任务或存档，必须二次确认。

Steam Build `24911270` 的游戏原生可生成字典共有 85 项（ID `0–85`，ID `30` 为空）。目录一次只显示一页，请使用 **PageUp / PageDown** 查看其余条目；鱼和武器会显示正确分类。

测试结束后，可在 `test-artifacts/` 中生成脱敏诊断包：

```powershell
uv run python -m howtofish_cheat.diagnostics collect
```

如果游戏已经由你启动并进入本地存档，可以使用无界面的单次集成探针：

```powershell
uv run python -m howtofish_cheat.spawn_probe --item-id 56 --confirm-live-spawn
```

探针不会启动游戏，只执行一次生成、等待并确认进程仍存活，然后恢复临时补丁；持久输出仍只写入项目内的诊断日志。

诊断包包含最新的训练器 JSONL 日志和仓库版本信息，不包含存档、完整 Unity 日志、聊天内容或凭据。

---

## 深度技术文档

关于逆向工程分析、FishNet 多人同步网络模型、Mono Runtime TLS 内部机制、JIT 蹦床与规避陷阱的详细说明，请参阅：

📖 **[技术深度剖析与架构文档 (Technical Deep Dive)](docs/TECHNICAL_DEEP_DIVE.md)**
