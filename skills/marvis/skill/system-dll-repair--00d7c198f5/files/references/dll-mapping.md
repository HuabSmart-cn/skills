# DLL / 错误码 → 修复工具 匹配表

本表用于修复流程 **第二步（匹配解决方案）**。优先级顺序：先 `runtime`，用户在第五步明确回复"修复失败（B）"后再切 `directx`；若第二步**只匹配到一个工具**（如只有 `runtime`），该工具修复失败后**兜底推荐另一款工具**（`runtime` 失败兜底推 `directx`，`directx` 失败兜底推 `runtime`）。两者（含兜底尝试）用户都回复 B 之后**先建议用户重启电脑或软件再尝试**，仍未解决则按企业现场支持卡片流程调用 MCP；资源不可用时静默省略卡片。

## 工具编号

- **runtime** = 微软常用运行库合集（`Microsoft Visual C++ Redistributable Runtimes.exe`，约 86 MB；下载较慢，需提示用户耐心等待）
- **directx** = DirectX Repair（增强版）（`DirectX Repair.exe`，约 1 MB）

---

## 1. 错误码匹配

| 错误码 / 报错提示 | 推荐工具（优先级） |
| :-- | :-- |
| 0xc000007b | runtime → directx |
| 0xc0000022 | runtime → directx |
| 0xc0000142（应用程序无法正确启动） | runtime → directx |
| 0xc0000135（应用程序无法正常启动；缺少 .NET / 运行库） | runtime |
| 0xc0000409（堆栈缓冲区溢出，常见于 Office / Outlook 自身 bug） | **不适用**（建议修复 / 重装报错软件本身，再不行先重启电脑或软件，最后输出统一结束语） |
| xxx.dll 没有被指定在 windows 上运行 | runtime → directx |
| 应用程序无法正常启动 | runtime → directx |
| 无法启动此程序，因为计算机中丢失 xxx.dll | 按 dll 名称匹配（见下） |
| 由于找不到 xxx.dll，无法继续执行代码 | 按 dll 名称匹配（见下） |

---

## 2. DLL 文件名匹配（VC++ / 通用运行库 → runtime）

| DLL 文件 | 归属运行库 | 推荐工具 |
| :-- | :-- | :-- |
| msvcp140.dll / vcomp140.dll / mfc140u.dll / vcruntime140.dll / vcruntime140_1.dll / concrt140.dll / ucrtbase.dll | VC++ 2015–2022 (14.x) | runtime |
| **vcomp140.dll**（OpenMP 并行计算运行时，VC++ 2015–2022 必备） | VC++ 2015–2022 (14.x) | runtime |
| api-ms-win-crt-runtime-l1-1-0.dll / api-ms-win-core-path-l1-1-0.dll | 通用 C 运行时 (UCRT) | runtime |
| msvcp120.dll / msvcr120.dll | VC++ 2013 (12.0) | runtime |
| msvcp110.dll / msvcr110.dll | VC++ 2012 (11.0) | runtime |
| msvcp100.dll / msvcr100.dll | VC++ 2010 (10.0) | runtime |
| msvcp90.dll / msvcr90.dll | VC++ 2008 (9.0) | runtime |
| msvcp80.dll / msvcr80.dll | VC++ 2005 (8.0) | runtime |
| mscoree.dll / system.web.dll / system.*.dll | .NET Framework | runtime |
| msvbvm50.dll / msvbvm60.dll | Visual Basic 5.0/6.0 运行库 | runtime |
| msxml4.dll / msxml6.dll | MSXML | runtime |
| atl*.dll（atl80/90/100/110.dll） | ATL（VC++ 配套） | runtime |
| mfc*.dll（mfc80/90/100/110/120.dll） | MFC 类库（VC++ 配套） | runtime |
| msdia*.dll | VC++ 调试组件 | runtime |

---

## 3. DLL 文件名匹配（DirectX 相关 → directx）

| DLL 文件（范围） | 组件类别 | 推荐工具 |
| :-- | :-- | :-- |
| d3dx9_24.dll ~ d3dx9_43.dll | DirectX 9 扩展工具库 | directx |
| d3dx10_36.dll ~ d3dx10_43.dll | DirectX 10 扩展工具库 | directx |
| d3dx11_42.dll / d3dx11_43.dll | DirectX 11 扩展工具库 | directx |
| d3dcompiler_33.dll ~ d3dcompiler_47.dll | D3DCompiler 着色器编译器 | directx |
| **d3dcompiler_43.dll**（DirectX 9/10 时代游戏最常缺失） | D3DCompiler 着色器编译器 | directx |
| **d3dcompiler_47.dll**（现代 DirectX 11/12 游戏） | D3DCompiler 着色器编译器 | directx |
| xinput1_1.dll ~ xinput1_4.dll | XInput（游戏手柄） | directx |
| dinput8.dll | DirectInput | directx |
| dsound.dll | DirectSound（基础音频） | directx |
| xaudio2_0.dll ~ xaudio2_8.dll | XAudio2（现代音频 API） | directx |
| **xapofx1_5.dll**（XAudio2 配套音频特效，常见于游戏与多媒体） | XAPOFX 音频特效 | directx |
| x3daudio1_0.dll ~ x3daudio1_7.dll | X3DAudio（3D 空间音频） | directx |
| d3d9.dll / d3d10.dll / d3d11.dll / d3d12.dll | Direct3D 核心运行时 | directx |
| dxgi.dll | DirectX 图形基础设施 | directx |
| ddraw.dll | DirectDraw（经典 2D 游戏） | directx |

---

## 4. 两款工具覆盖重叠

`DirectX Repair（增强版）` 具备 **C++ 强力修复** 功能，能兼顾大多数 VC++ 运行库 dll 问题。
因此当 `runtime` 修复无效时，可指引用户再尝试 `directx` 的强力修复 + C++ 强力修复。

## 5. 匹配不到时

当上述条目均无法命中用户报错信息时，进入修复流程第二步 B 路径——**不提供任何修复工具**，提示用户未能匹配到合适的解决方案，**先建议用户重启电脑或软件再尝试**；若仍未解决，在最终报告前执行**企业现场支持卡片流程**：

> 最终报告前按 `SKILL.md` 的企业现场支持卡片流程调用 MCP；资源不可用时静默省略卡片。

### 5.1 已知不适用 DLL 速查清单（不要尝试修复工具，先建议重启再输出结束语）

以下 DLL 属于**第三方应用自带的私有运行库**，不在两款修复工具的修复范围内，命中时应**跳过工具推荐直接转人工**：

| DLL 文件 | 来源 | 备注 |
| :-- | :-- | :-- |
| libeay32.dll / ssleay32.dll | OpenSSL 1.0.x | 第三方加密库，需重装应用或单独补 OpenSSL |
| libcrypto-*.dll / libssl-*.dll | OpenSSL 1.1.x / 3.x | 同上 |
| Qt5Core.dll / Qt5Gui.dll / Qt5Widgets.dll / Qt6*.dll | Qt 应用框架 | 需重装应用或补 Qt 运行库 |
| python3*.dll / pythonXY.dll | Python 解释器 | 需重装 Python |
| node.dll / v8*.dll | Node.js / Electron | 需重装应用 |
| zlib1.dll / libcurl.dll / libxml2.dll | 第三方开源库 | 需重装应用 |
| **msls70.dll / pagelayout.dll**（Outlook / Word 启动报错） | Office 自带私有 DLL | Office 通道版本不匹配引起，需重装/修复 Office，**不要用 runtime/directx** |
| **AppVIsvSubsystems32.dll**（Office 启动报错） | Office App-V 子系统 | 需快速修复 / 在线修复 Office |
| **OLMAPI32.dll**（Outlook 崩溃 0xc0000409） | Outlook MAPI 实现 | 需更新 Office 至已修复版本 |
| **PhysX*.dll / NxCooking.dll**（游戏场景） | NVIDIA PhysX 物理引擎 | 需安装 NVIDIA PhysX System Software |
| **XnaNative.dll / Microsoft.Xna.Framework*.dll** | XNA Framework | 需安装 Microsoft XNA Framework Redistributable |
| **steam_api.dll / steam_api64.dll** | Steam SDK | Steam 游戏私有库，需修复/重装 Steam 或该游戏 |
| **EAAntiCheat / BattlEye / EasyAntiCheat 相关 DLL** | 反作弊组件 | 需通过游戏自身重装反作弊组件 |
| 游戏 / 软件安装目录下的私有 DLL | 应用自带 | 需重装或修复该应用 |

> **判定原则：** 凡是**不在第 2/3 节中显式列出**且**不属于 VC++/DirectX/.NET/UCRT/VB/MSXML 任一类别**的 DLL，都应按本节处理——**不要尝试 runtime / directx 工具**，先建议用户重启电脑或软件再尝试，仍未解决则在最终报告前执行企业现场支持卡片流程。

## 6. 匹配算法（供 skill 执行时参考）

1. 提取用户输入（文字或图片 OCR 文本）中的 **dll 文件名** 与 **错误码**；
2. 依次在第 1/2/3 节中查找命中项；
3. 若命中任意一项，返回对应工具编号（`runtime` / `directx`）；
4. 若同时命中多类，按 **runtime → directx** 顺序优先推荐；若只命中一类，该工具修复失败后**兜底推荐另一款工具**（`runtime` 失败兜底推 `directx`，`directx` 失败兜底推 `runtime`）；
5. 未命中则进入第 5 节分支（先建议重启电脑/软件再尝试，仍未解决则输出统一结束语）。
