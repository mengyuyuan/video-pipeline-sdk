# Changelog

## v0.2.1 — 2026-09-16（深夜）

- 弹药仓 +2：`assets/fx/FxPanel3D.tsx`（FX-15 真透视 3D 卡 · 融入现实斜面板）/ `assets/fx/FxBehindMask.tsx`（FX-16 人物蒙版分层 · 背后物件与文字穿人的底座件）——均为真片生产验证件
- 工具 +2：`tools/rvm_matte.py`（RVM 抠像出 RGBA 序列）/ `tools/make_masks.py`（逐帧 PNG 蒙版 · 收紧配方），补齐"空间融合"资产链
- PITFALLS 增补：同文件重复导出同名符号 → 整个 Studio 白屏；无头截屏采样漂移 → 元素核验改用精确单帧
- quality-mechanisms：成组入场节奏（逐项 stagger ≤4 帧/项，整组台词窗口前 1/3 就位）
- 二次生产验证：34s / 4K60 HEVC 源口播全流程一次通过（摸底→转录→设计表→写码→蒙版→音效→预览）

## v0.2.0 — 2026-09-16

- 真片全流程实跑收官（110s / 25 场 / 3313 帧 / Remotion 4.0.503）并把全部经验回灌产线
- 新增 `PITFALLS.md`：音画同步三级偏移、渲染基建（bundle 复用 / 静帧假 OK）、OffthreadVideo 关键帧、字幕子词修正、工程坑总表
- 新增工具：`check_sync.py`（互相关同步核验，实测 0.0ms）、`transcribe.py`、`transcode_material.py`、`build_scenes_data.py`、`clean_remotion_temp.ps1`
- RUNBOOK Step 8/9 升级：预览近似同步注意 + 渲染基建（bundle 复用）+ 音频处理链裁齐 + 同步交付门
- 开源准备：MIT License；ATTRIBUTIONS 复核（受限资产不入库）；scratch 脚本清理

## v0.1.0 — 2026-09-16

- 骨架：九步 RUNBOOK、七件核验门（含自检）、弹药仓（fx 17 件 / 字体 / LUT / 音效 / 素材台账）、Remotion 依赖蓝本、INTERFACE 契约
