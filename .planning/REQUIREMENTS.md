# Requirements: WhisperKey — Recording Overlay UI

**Defined:** 2026-03-09
**Core Value:** 按住热键说话，松开就出现文字——零延迟感、零打断工作流。

## v1 Requirements

### Overlay Foundation

- [ ] **OVL-01**: 录音中，屏幕底部居中显示半透明圆角浮层（NSPanel，常驻最顶层，点击穿透）
- [ ] **OVL-02**: 浮层出现时不抢夺焦点，不打断用户当前文字输入
- [ ] **OVL-03**: 浮层在所有 Space 可见（Mission Control 切换不消失）

### Recording State

- [ ] **REC-01**: 录音期间浮层显示动态波形动画（4-6 bars，~30fps，idle sine-wave）
- [ ] **REC-02**: 浮层出现动效：150ms fade-in + 8pt 上滑，ease-out

### Transcribing State

- [ ] **TRN-01**: 松开热键后，浮层切换到"转录中"状态，显示 3 dots 脉冲动画（300ms/dot，900ms 全循环）
- [ ] **TRN-02**: 录音状态平滑切换到转录中状态（无闪烁）

### Result State — Text Input Branch

- [ ] **RST-01**: 转录完成，若光标在文字输入框，静默注入文字，浮层 200ms fade-out 消失

### Result State — Clipboard Branch

- [ ] **RST-02**: 转录完成，若光标不在文字输入框，浮层显示转录文字内容
- [ ] **RST-03**: 浮层同时显示"已复制到剪贴板"提示文字
- [ ] **RST-04**: 3 秒后浮层 400ms fade-out 消失

### Text Input Detection

- [ ] **DET-01**: 使用 macOS Accessibility API 判断当前焦点是否在文字输入框（AXRole 匹配 AXTextField / AXTextArea / AXComboBox / AXSearchField）
- [ ] **DET-02**: Accessibility API 失败或返回 None 时，默认走剪贴板路径（安全降级）

## v2 Requirements

### Visual Enhancement

- **VIS-01**: 波形改为 RMS 驱动（实时音频振幅），替代 idle sine-wave
- **VIS-02**: 多显示器支持——浮层跟随当前活跃窗口所在的屏幕

## Out of Scope

| Feature | Reason |
|---------|--------|
| 菜单栏图标变化 | 有浮层已足够，避免冗余 |
| 可拖动浮层 | solo 用户不需要，增加状态复杂度 |
| 转录历史记录 | 超出本次功能范围 |
| 流式局部转录（streaming） | faster-whisper 返回完整结果；伪造 streaming 有误导性 |
| 声音效果 | 未请求 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| OVL-01 | Phase 1 | Pending |
| OVL-02 | Phase 1 | Pending |
| OVL-03 | Phase 1 | Pending |
| REC-01 | Phase 3 | Pending |
| REC-02 | Phase 3 | Pending |
| TRN-01 | Phase 3 | Pending |
| TRN-02 | Phase 3 | Pending |
| RST-01 | Phase 2 | Pending |
| RST-02 | Phase 2 | Pending |
| RST-03 | Phase 2 | Pending |
| RST-04 | Phase 2 | Pending |
| DET-01 | Phase 2 | Pending |
| DET-02 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after initial definition*
