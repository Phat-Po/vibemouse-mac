# WhisperKey

## What This Is

WhisperKey 是一个 macOS 本地离线语音输入工具。按住热键录音，松开后自动转录并注入文字到当前应用。基于 faster-whisper，无需联网、无订阅费用，支持中英文混合识别。目标用户是自己（solo 使用场景）。

## Core Value

按住热键说话，松开就出现文字——零延迟感、零打断工作流。

## Requirements

### Validated

- ✓ 按住 Right Option 录音，松开触发转录并注入文字 — MVP
- ✓ Hands-free 模式（Option + Command 切换持续录音）— MVP
- ✓ 支持中文、英文及 90+ 语言 — MVP
- ✓ 完全离线运行（首次联网下载模型后） — MVP
- ✓ 转录结果自动复制到剪贴板并注入当前 app — MVP
- ✓ 交互式双语设置向导（zh/en） — MVP
- ✓ macOS LaunchAgent 开机自启动 — MVP
- ✓ 自定义热键配置 — MVP
- ✓ `whisperkey help` 诊断命令 — MVP

### Active

- [ ] 录音时在屏幕底部居中显示动态录音浮层（类似 AquaVoice 麦克风波形动画）
- [ ] 转录完成后，若光标在文字输入框：静默注入文字，浮层消失
- [ ] 转录完成后，若光标不在输入框：浮层显示转录文字 + "已复制到剪贴板"，3 秒后淡出消失

### Out of Scope

- 菜单栏图标变化 — 有浮层已够，避免重复
- 转录历史记录 — 当前阶段不需要
- 多语言 UI 切换（浮层固定中文即可）— 简化实现

## Context

- 现有 MVP 已在本地 macOS 稳定运行，后台 LaunchAgent 已配置
- 包名：`whisperkey-mac`，CLI 入口：`whisperkey`
- 代码结构：`whisperkey_mac/`（main.py、keyboard_listener.py、audio.py、transcriber.py、output.py 等）
- 目前误触 hands-free 模式的问题是核心痛点，浮层 UI 可提供视觉反馈，降低误操作
- 技术栈：Python 3.10+，macOS AppKit/PyObjC 可用于浮层 UI
- GitHub：https://github.com/Phat-Po/whisperkey-mac

## Constraints

- **Platform**: macOS only — 浮层 UI 使用 macOS 原生框架
- **Language**: Python — 保持和现有代码库一致，不引入新语言
- **No bundling**: 不打包成 .app，仍以 pip install / python -m 方式运行

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 浮层使用 PyObjC/AppKit 实现 | Python 原生 tkinter 难以做透明浮层，AppKit 是 macOS 标准 | — Pending |
| 底部居中，半透明圆角 | 类 AquaVoice 设计，不遮挡主要工作内容 | — Pending |

---
*Last updated: 2026-03-09 after initialization*
