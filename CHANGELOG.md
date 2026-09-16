# Changelog

## v0.2.0 — 2026-09-16

- 真片全流程实跑收官（110s / 25 场 / 3313 帧 / Remotion 4.0.503）并把全部经验回灌产线
- 新增 `PITFALLS.md`：音画同步三级偏移、渲染基建（bundle 复用 / 静帧假 OK）、OffthreadVideo 关键帧、字幕子词修正、工程坑总表
- 新增工具：`check_sync.py`（互相关同步核验，实测 0.0ms）、`transcribe.py`、`transcode_material.py`、`build_scenes_data.py`、`clean_remotion_temp.ps1`
- RUNBOOK Step 8/9 升级：预览近似同步注意 + 渲染基建（bundle 复用）+ 音频处理链裁齐 + 同步交付门
- 开源准备：MIT License；ATTRIBUTIONS 复核（受限资产不入库）；scratch 脚本清理

## v0.1.0 — 2026-09-16

- 骨架：九步 RUNBOOK、七件核验门（含自检）、弹药仓（fx 17 件 / 字体 / LUT / 音效 / 素材台账）、Remotion 依赖蓝本、INTERFACE 契约
