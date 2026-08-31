# How to Fish Trainer — Xocks External Edition v0.3.0

这是基于 `fredwangwang/how-to-fish-trainer` 的 Xocks 社区改版正式发布。它是独立运行的外置程序，不向游戏目录安装 DLL，也不替换游戏文件。

## 这一版有什么不同

- 运行时读取游戏官方物品 ID，并合并隐藏 Item 与安全引擎预览，不依赖手写死列表。
- F7/F8 物品选择与生成，包含角色/网络对象硬阻止、危险物品确认和单次按键去重。
- F9 360°最近目标锁定，支持鱼、鸟、其他生物和私房玩家开关。
- F11 最高 60 FPS 的物品/生物 ESP，字体大小与显示距离可调。
- Home 肩后第三人称，使用游戏原生 `PlayerLegs -> PlayerHands -> PlayerBody -> IK` 展示数据，不使用手写假步态。
- End 静默自瞄、网络姿态与普通客户端能力作为好友/私房实验功能，界面会明确显示服务器认可仍待实测。
- Insert 鼠标控制面板、响应式物品列表、中英文界面和脱敏诊断包。
- F10、Ctrl+C 和异常退出会恢复机器码补丁、相机、输入、渲染器与临时引用。

## 下载与使用

下载 `HowToFishTrainer-v0.3.0-win64.zip` 或单文件 EXE。建议先完全退出旧修改器和游戏，再启动游戏与本版本，避免 Mono 继续保留旧辅助程序集。

物品生成请优先使用临时存档、单人游戏或房主环境。玩家目标、静默弹道和姿态实验只用于好友明确同意的私房测试。

## 校验

`HowToFishTrainer-v0.3.0-win64.exe`

```text
SHA-256: 0CD37C642DEC07E3B7272D9E448E6BF7FE5E7364A501A7991FF09DF098E28E94
```

`HowToFishTrainer-v0.3.0-win64.zip`

```text
SHA-256: 14CF8E31D4E48A81667714FEEE44FA9962EE8822D4FD9FC6B369663AC4468C91
```

## 验证范围

- 自动化测试：92 项全部通过。
- 最终 DLL、EXE 内嵌程序集和 ZIP 内容已完成一致性检查。
- 自动化测试不等同于所有游戏更新、所有物品、服务器弹道认可、远端姿态或命中箱均已实测。

感谢上游作者 Huan Wang / fredwangwang。项目继续使用 MIT License。
