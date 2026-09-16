# 坑位总表（PITFALLS）

> 血账换来的实操坑位，按主题分组：**现象 → 根因 → 修法**。
> 最新一批来自《大模型魔幻发展史》v2 真片全流程实跑（110s / 25 场 / Remotion 4.0.503，2026-09）。

## 1. 音画同步（三级偏移，交付前必查）

| 现象 | 根因 | 修法 |
|------|------|------|
| 成片音频比画面晚 ~30ms | 音频处理链（afftdn / loudnorm / alimiter）引入整体后移 | 用 `tools/check_sync.py` 互相关实测偏移（ms 级），以 `atrim=start_sample=N` 裁齐（48kHz 下 30ms = 1440 samples），复核归零 |
| 成片音频再晚 ~42.6ms | Remotion 输出 AAC 编码固有延迟（2048 samples @48k），直接 remux 不自动补偿 | 渲染后抽声实测 → 裁齐重封（`-c:v copy -c:a aac`）→ 复核 `|偏移| ≤ 15ms` 才算交付（实测可收敛到 0.0ms） |
| Studio 预览"声音和嘴唇对不上"（200-600ms 浮动） | Studio 播放器是近似同步（音频元素起步晚于视频元素，播放中不强制校正） | 审片用「拖时间轴定位 / 暂停再播」（收拢到 ~70ms）与帧步进；**同步判定以渲染件互相关实测为准，不以预览观感为准** |
| 蓝牙耳机审片总觉得偏 | 蓝牙链路叠加 150-300ms 输出延迟 | 验同步换有线/音箱 |

核验命令（`tools/check_sync.py`，依赖 numpy；参考音频建议从原片直抽）：

```bash
python tools/check_sync.py --ref ref.wav --test out.mp4 --windows 8-14,30-36,60-66
```

## 2. 渲染基建（Windows 专项）

| 现象 | 根因 | 修法 |
|------|------|------|
| 渲染/静帧突然 ENOSPC、C 盘爆满 | 每次 `remotion render/still` 都会把整个 `public/` 拷进系统 Temp（素材多的工程单次 ~1GB） | ① `npx remotion bundle` 一次到项目内 `build/`，之后 `npx remotion render build <Comp>` 复用（每次省一遍全量拷贝）；② `TEMP`/`TMP` 重定向到大盘；③ 定期清 `Temp/remotion-v4.0.503-assets*`（`tools/clean_remotion_temp.ps1`） |
| 静帧检查"全绿"但其实是旧帧 | 渲染失败时旧文件仍在，只查"文件存在"会把失败伪装成 OK | 渲染前先 `rm` 目标文件，再渲、再查存在性 |
| Studio 假死 / 热更新通知风暴 | Studio 长时间挂着 + 高频改动 | 渲染前重启 Studio；预览端口固定 3002（3000/3001 留给宿主） |

## 3. 素材与 OffthreadVideo

- **关键帧**：素材转码必须 `-g 30 -keyint_min 30 -sc_threshold 0`（每秒一个关键帧），OffthreadVideo 逐帧 seek 才精确且快；否则渲染慢或抽错帧。
- **转码基线**：`fps=30` + `scale=1920:1080:force_original_aspect_ratio=decrease` + `pad`（等比缩放补边，不拉伸）；脚本 `tools/transcode_material.py`。
- **PiP 小窗**：OffthreadVideo 不给显式 `width/height` 会被容器裁空白——必须显式尺寸。
- **4K60 HEVC 源**：解码慢（几分钟素材可转分钟级），转码放后台队列挨个过。

## 4. 转录与字幕

- **whisper 子词 token 陷阱**：英文/数字会被拆成子词（`F`+`avor`+` 5`），逐 token 修正匹配不上。做法：拼回整串 → 场景级整串替换（含跨段合并，如 `用他¦设置` → `用它试试`）→ 按字符时间映射重建词级时间轴。参考实现：`tools/build_scenes_data.py`。
- **展示标点**：段边界可插逗号提升可读性；跨段连读短语用 skip 表关掉该逗号（防"再给他，一些时间"式断句）。
- **错字修正三处同步**：改一处要同步 transcript / SCENES / 卡片文案，防三处不一致。
- **慎用 VAD**：软语音会被当静音切掉——口播默认关 VAD + 词级时间戳即可。

## 5. 工程与工具链

- **JSX 里的复杂模板字符串**：esbuild 在嵌套模板字符串/对象混排时易炸（`Expected ">" but found "<"`）——跨行动态值尽量提为静态字符串或变量。
- **颜色助手别混 CSS 写法**：自定义 `rgba(hex, a)` 助手混入 CSS 四参写法（`rgba(255,255,255,0.1)`）会 `hex.replace is not a function`。
- **Python 子进程调 npx**：Windows 用 `shutil.which("npx.cmd")` 拿全路径，裸名找不到。
- **PowerShell 5.1 中文脚本**：.ps1 含中文必须存 UTF-8 BOM，否则解析炸。
- **改前先读**：编辑既有文件前先读磁盘现状取锚点（外部工具/协作者可能已改过），否则批量替换会错配。
