# 渔力全开 (How to Fish) - Xocks 外置辅助改版

[English](README.md) | [简体中文](README_zh.md)

专为 Unity Mono 引擎游戏 **[渔力全开 (How to Fish)](https://store.steampowered.com/)** 打造的外置修改器：**不安装 Mod、不替换游戏文件**，运行时连接 Mono，提供自动物品目录、原生动作链第三人称、锁头、静默自瞄、物品/生物透视与安全诊断。

> [!IMPORTANT]
> 这是 **Xocks 维护的社区改版**，基于
> **[fredwangwang/how-to-fish-trainer](https://github.com/fredwangwang/how-to-fish-trainer)**
> 的 `688a9c9` 版本继续开发，并非原作者发布的官方新版。原项目版权与
> MIT 许可声明均予以保留。

- **改版仓库：** [Xocks/how-to-fish-trainer](https://github.com/Xocks/how-to-fish-trainer)
- **当前唯一分支：** [`main`](https://github.com/Xocks/how-to-fish-trainer/tree/main)
- **当前发布版本：** `0.3.0`

基于 `pymem` 与底层 Mono Runtime C API 互操作实现 JIT 函数 Hook / 机器码补丁，并提供 `rich` 现代化交互式终端控制面板，支持中英文双语无缝切换与免 Python 单文件 `.exe` 运行。

> **v0.3.0：** 核心代码、兼容门禁、可逆恢复、运行时目录、锁头、透视和第三人称原生展示链已经通过自动化测试及最终 DLL/EXE 构建。静默弹道、网络姿态、玩家目标和普通客户端能力仍属于私房实验功能，服务器是否认可必须以双客户端实测为准。

---

## 这个改版新增了什么

相对原版，本分支主要加入以下功能与稳定性改进：

| 改版内容 | 说明 |
| :--- | :--- |
| **F7 运行时物品目录** | 先显示游戏自己的 `GameInfo.GetSpawnable(byte)` 官方 ID，再合并名称/皮肤、资源 Item 与引擎对象并分配 1000 以上的选择 ID；游戏重连后重新扫描。 |
| **F8 原生物品生成** | 调用游戏原生 `DazedCommands.UseSpawnCommand`，在相机前方约 2 米生成当前物品；限制为单人游戏或房主，并带有 500ms 防连点。 |
| **分层物品目录** | Insert“生成器”按官方可拾取物、隐藏 `Item`、可见模型预览和仅诊断资源分层；底层 Unity 对象不再全部冒充可生成物品。 |
| **特殊物品保护** | 只有真实任务物品和爆炸物要求再次确认；角色、网络管理对象和无可复制渲染内容的资源永久禁止。引擎模型预览不可拾取且不会联网同步。 |
| **角色生成硬阻止** | ID 53“角色”、`deadplayer` 和带 `DeadPlayer` 组件的网络角色显示红色 `×`，无法选择或生成，避免缺少玩家状态时闪退。 |
| **新版兼容门禁** | 校验程序集 SHA-256、Mono 方法/字段契约和 JIT 入口；未知版本只输出诊断，不安装补丁。 |
| **F9 枪械锁头** | 持枪 ADS 并按住右键时，360°按世界距离选择最近的已启用目标；默认鱼和鸟，其他生物可选，玩家默认关闭且每次运行都要确认好友/私房。 |
| **Home 第三人称** | 保留已经产生真实位移的 `CurCam` 肩后相机；从玩家 Prefab 重建拥有者被隐藏的渲染层级，并临时把游戏保留的 `PlayerLegs`、`PlayerHands`、`PlayerBody` 与 `IK` 原生展示链绑定到该层级。v0.3.0 使用真实移动、持有物、相机、呼吸、地面和船只状态，不再使用手写步态；退出时还原全部引用。不复制玩家、网络、碰撞或刚体脚本。本机画面不等于其他客户端画面或命中箱变化，仍需双客户端验证。 |
| **End 静默自瞄（实验）** | 无需按住右键即可预锁目标，不移动镜头；新生成的本地弹丸会先校正一次方向，追踪模式随后限速转向并在遮挡后停止。网络认可仍待私房实测。 |
| **私房姿态实验** | “低头朝后”和“高速身体转圈”是两个互斥模式，只在游戏原有姿态发送窗口临时替换旋转并立即恢复本地视角；远端动画和命中箱仍需双客户端验证。 |
| **F8 单次触发** | F8 改为松开按键时触发并增加 400ms 请求去重；按住按键不会重复创建对象或刷屏日志。 |
| **F11 物品/生物标签** | 标签位置最高 60 FPS 更新，遮挡查询分批执行；字体可在 10–36 调整。 |
| **Insert 鼠标面板** | 新增生成器标签页；打开时暂停游戏视角和鼠标开火输入，关闭后精确恢复。 |
| **普通客户端实验请求** | 不伪造房主权限；仅在私有测试确认后通过游戏现有 `Server.BuyItem` RPC 请求安全普通物品或枪械，2 秒限速并在不同步时失败关闭。 |
| **崩溃修复** | 生成调用被调度到 Unity 主线程；加入双向恢复握手，并让固定的 Mono 字符串在当前游戏进程生命周期内安全缓存，避免已定位的释放时序崩溃。 |
| **响应式物品 UI** | 大窗口每行显示四组“ID / 物品”并利用可用高度增加每页容量；窄窗口自动降为三、二或一组，缩放后整屏重绘。 |
| **诊断与测试工具** | 新增脱敏诊断包、单次 `spawn_probe` 集成探针，以及目录、选择器、权限、限速、重连和主线程恢复等自动化测试。 |

这仍是外部进程内存修改器：不替换游戏文件，也不是安装到游戏目录的 Mod。物品生成器涉及游戏对象创建，请优先在临时存档、单人游戏或房主环境中使用。

准备录制介绍视频时，可直接使用：

🎬 **[视频标题、简介与演示文案](docs/VIDEO_DESCRIPTION_ZH.md)**

---

## 功能特性

| 快捷键 | 功能名称 | 详细说明 |
| :--- | :--- | :--- |
| **F1** | **锁定生命** | 单人/房主为完整保护；普通客户端拦截本地伤害报告与异常状态并显示“部分保护”，服务器直接裁决的伤害不承诺免疫。 |
| **F2** | **锁定饱食度** | 阻止饱食度随时间自然流逝或因行为动作消耗，永久维持满腹状态。 |
| **F3** | **无限空中跳** | 纯跳跃逻辑补丁：允许在空中无限次连跳与凌空飞行（**不启用 InGodMode，不影响血量逻辑**）。 |
| **F4** | **无限弹药** | 所有枪械无限备弹与弹匣容量，射击不消耗子弹，无需频繁换弹。 |
| **F5** | **伤害倍率** | 循环切换枪械、近战武器与徒手拳头的伤害倍率：**`1x` $\rightarrow$ `2x` $\rightarrow$ `5x` $\rightarrow$ `10x` $\rightarrow$ `一击必杀 (99999)`**。 |
| **F6** | **增加金币 (+1w)** | 每次按下立即增加 **+$10,000 (1万)** 金币，附带金币音效、飘字动画与 HUD 数字滚动效果，并同步至联机网络。 |
| **F7** | **选择生成物品** | 官方物品使用原 ID，隐藏/资源/引擎条目使用 1000 以上的合成 ID；红色 `×` 表示禁止，红色 `!` 表示二次确认。 |
| **F8** | **生成当前物品** | 单人/房主在前方生成；普通客户端仅在私有实验开关打开时请求安全物品直接到手。 |
| **F9** | **360°枪械锁头** | 默认按世界距离选最近的鱼或鸟；Insert 可另开其他生物，玩家开关与 End 共用并要求私房确认。 |
| **Home** | **第三人称** | 开关带墙体碰撞缩距的肩后相机与本机角色渲染镜像；镜像状态、网格和骨骼计数在诊断页显示。 |
| **End** | **静默自瞄（实验）** | 镜头不跟随目标；使用原开火方向或本地实体弹丸转向，普通客户端必须先确认私房测试。 |
| **F11** | **物品 / 生物透视** | 开关最高 60 FPS 的名称、距离、分类颜色和遮挡变暗标签。 |
| **Insert** | **鼠标控制面板** | 战斗、透视、生成器、实验、诊断；面板打开时视角不会随鼠标移动。 |
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
   - **物品生成器 (`F7` / `F8`)**：Unity 主线程合并官方 ID、名称字典、`Resources/Items` 和引擎预制体目录；热键线程只排队，实际生成在 managed `Update` 执行。普通客户端仍不伪造 `IsServerInitialized`。
   - **锁头 / ESP (`F9` / `F11`)**：外部控制器将仓库内辅助程序集临时加载进当前 Mono 域。Unity 主线程执行 360°目标选择、两层后坐力补偿、对象扫描和 60 Hz 投影；辅助程序集不复制到游戏目录。
   - **安全还原**：关闭功能或退出修改器时，自动恢复原始机器码字节与伤害基准值。

3. **现代化终端 UI (`howtofish_cheat.ui.console`)**：
   - 基于 `rich` 构建的高刷新率仪表盘，实时展示游戏连接状态、进程 PID、Mono 域指针与各项功能开关。

---

## 使用指南

### 1. 获取并运行修改器

#### 方式 A：直接下载预编译独立可执行程序（推荐）
从 **[Xocks 改版 Releases](https://github.com/Xocks/how-to-fish-trainer/releases)** 下载带有 `Xocks` 或 `v0.3.0` 标识的改版构建。不要把原作者仓库中的旧版本误认为包含锁头和透视。单文件 `.exe` 无需安装 Python。

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
- 按 **F9** 开关枪械锁头，持枪 ADS 时按住鼠标右键生效
- 按 **Home** 开关第三人称相机
- 按 **End** 开关静默自瞄实验；在 Insert 面板选择开火修正或实体弹丸追踪
- 按 **F11** 开关物品 / 生物标签
- 按 **Insert** 打开或关闭鼠标控制面板
- 按 **F12** 随时 **切换语言 (中文 / English)**
- 按 **F10** / **ESC** / **Ctrl+C** 安全退出修改器

### 3. 物品生成器测试与诊断

首次测试请使用新建的临时存档。先在单人模式分别验证一条鱼和一把枪，再用第二个客户端验证房主生成后的可见性与拾取同步。只有真实任务物品和爆炸物要求确认。“可见模型预览”只复制静态 Mesh/Sprite，不运行原 Prefab 脚本，不能拾取也不会联网同步；“仅诊断资源”不能生成。

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

---

## 致谢与许可

- **原项目：** [fredwangwang/how-to-fish-trainer](https://github.com/fredwangwang/how-to-fish-trainer)
- **改版维护：** [Xocks/how-to-fish-trainer](https://github.com/Xocks/how-to-fish-trainer)
- 项目继续遵循仓库中的 [MIT License](LICENSE)。分发修改版源码或程序时，请保留原版权与许可声明。
- 本项目与游戏开发商、发行商和 Steam 均无隶属或官方合作关系。
