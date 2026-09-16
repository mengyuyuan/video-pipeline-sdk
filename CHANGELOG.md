# Changelog

## v0.3.0（开发中）· 独立接口本体 P2

- 新 `pipeline/run.py`：单入口 stage 机（十段：ingest→transcribe→scenes→design-table→scaffold→build→verify→preview→render→deliver）＋两道确认门（checkpoint-1 设计表 / checkpoint-2 预览）＋退出码（0 完成 / 2 门失败 / 3 待作答 / 1 异常）＋断点续跑（run-state.json）
- 新 `pipeline/ask.py` + `assets/cards/index.html`：问题协议（多选/单选/审批/自由文本 + 预览图）＋本地卡面服务（默认 8898，占用自动 +1，避开端口矩阵）＋ `--emit` 交宿主渲染
- 新 `pipeline/doctor.py`：环境自检（硬依赖 / 软依赖分级）
- 新 `gates/aggregate.py`：七件门聚合，verify / render 双相 + 报告按 id 合并 → gate-report.md/json
- 卡面/协议边界：宿主只经 questions.json / answers/<id>.json 对接（协议是脊柱，界面只是渲染器）
- 冒烟验证：全流程 3→3→3→0（两次停门、两次放行、完成交付五件套 + manifest）；卡面 e2e 通过

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
