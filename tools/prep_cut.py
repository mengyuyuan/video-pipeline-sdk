#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频产线 SDK · 智能粗剪（Step 0.5：粗剪先行再包装）

配方（用户 2026.9.8 立，本文件为此配方的唯一实现）：
  剪气口：silencedetect -32dB / d=0.7s，>0.7s 停顿剪到保留 0.22s 呼吸；段内全处理。
  钩子前置：按词级时间戳把最炸句整段剪到开头；原位置剔除（禁重复画面）。
  额外删除：plan.extra_cuts（口误/重复，人工/执行者指定）。
  合成：多段 filter_complex，全部段引用 [0:v]/[0:a]；trim/atrim+setpts/asetpts → concat；re-encode libx264 crf20。
  时间轴全重建：cut.mp4 + 新 transcript + 粗剪清单；下游一切以新轴为准。

用法：
  python tools/prep_cut.py --proxy P --transcript T --plan PLAN.json --out-dir OUT
  python tools/prep_cut.py --proxy P --transcript T --out-dir OUT            # 无 plan：只剪气口，不前置

plan 结构：
  {
    "hook": {"start": 3.28, "end": 6.14, "text": "比如说打个小点这里出现一个3D卡片", "reason": "..."} | null,
    "extra_cuts": [{"start": 11.2, "end": 12.9, "reason": "口误"}],
    "silence": {"noise_db": -32, "min_d": 0.7, "breath": 0.22}
  }
  钩子句起止必须取自转录的句子边界（可用词级时间戳微调）。

产出（out-dir）：
  cut.mp4            粗剪后视频（音频未做 loudnorm，后处理链在渲染段）
  transcript.json    重映射转录（词级；被切开的长句按词边界拆成多条字幕）
  cut-list.md        粗剪清单（人审用：钩子/剪掉的气口/额外删除/对账）
  cut-report.json    机器对账（原时长/新时长/移除表/钩子/保留表）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK, EXIT_ERR = 0, 1


def log(msg: str) -> None:
    print(f"[prep_cut] {msg}", flush=True)


def die(msg: str) -> None:
    print(f"[prep_cut][error] {msg}", file=sys.stderr, flush=True)
    sys.exit(EXIT_ERR)


def run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe_duration(p: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)])
    try:
        return float(r.stdout.strip())
    except Exception:
        die(f"ffprobe 读不出时长：{r.stdout} {r.stderr[:200]}")


def detect_silences(proxy: Path, noise_db: float, min_d: float) -> list[tuple[float, float]]:
    r = run(["ffmpeg", "-v", "info", "-i", str(proxy), "-af", f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"])
    txt = (r.stdout or "") + (r.stderr or "")
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([\d.]+)", txt)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([\d.]+)", txt)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        if e is not None and e > s:
            out.append((s, e))
    return out


def merge_intervals(iv: list[tuple[float, float]]) -> list[tuple[float, float]]:
    iv = sorted((a, b) for a, b in iv if b - a > 0.02)
    out: list[list[float]] = []
    for a, b in iv:
        if out and a <= out[-1][1] + 0.001:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def complement(removals: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    keep, cur = [], 0.0
    for a, b in removals:
        if a > cur + 0.02:
            keep.append((cur, min(a, duration)))
        cur = max(cur, b)
    if cur < duration - 0.02:
        keep.append((cur, duration))
    return keep


def main() -> None:
    ap = argparse.ArgumentParser(description="视频产线 SDK · 智能粗剪（Step 0.5）")
    ap.add_argument("--proxy", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--plan")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    proxy = Path(args.proxy).resolve()
    tr_p = Path(args.transcript).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not proxy.is_file():
        die(f"代理不存在：{proxy}")
    if not tr_p.is_file():
        die(f"转录不存在：{tr_p}")

    plan = {"hook": None, "extra_cuts": []}
    if args.plan:
        p = Path(args.plan)
        if not p.is_file():
            die(f"plan 不存在：{p}")
        plan.update(json.loads(p.read_text(encoding="utf-8")))
    sil_cfg = {"noise_db": -32.0, "min_d": 0.7, "breath": 0.22}
    sil_cfg.update(plan.get("silence") or {})

    if plan.get("skip"):
        import shutil as _sh
        out_mp4 = out / "cut.mp4"
        _sh.copy(proxy, out_mp4)
        _sh.copy(tr_p, out / "transcript.json")
        reason = plan.get("reason", "")
        (out / "cut-report.json").write_text(json.dumps(
            {"skipped": True, "reason": reason}, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "cut-list.md").write_text(
            f"# 粗剪清单（Step 0.5）\n\n- 本片跳过粗剪（plan.skip=true）：原片照用，未做任何裁切。\n- 理由：{reason or '（未写）'}\n",
            encoding="utf-8")
        log("skip=true：原片照用，未做任何裁切")
        return

    tr = json.loads(tr_p.read_text(encoding="utf-8"))
    duration = float(tr.get("duration") or probe_duration(proxy))

    # ---- 1) 气口 ----
    silences = detect_silences(proxy, sil_cfg["noise_db"], sil_cfg["min_d"])
    breath = sil_cfg["breath"]
    removals: list[tuple[float, float]] = []
    sil_rows = []
    for s, e in silences:
        cut_s = s + breath
        if e - cut_s > 0.05:
            removals.append((cut_s, e))
            sil_rows.append({"start": round(s, 3), "end": round(e, 3), "kept_breath": breath, "removed": round(e - cut_s, 3)})
    log(f"气口：检出 {len(silences)} 处，剪掉 {sum(r['removed'] for r in sil_rows):.2f}s（阈值 {sil_cfg['noise_db']}dB / {sil_cfg['min_d']}s → 留 {breath}s）")

    # ---- 2) 额外删除（口误/重复）----
    extra_rows = []
    for c in plan.get("extra_cuts") or []:
        a, b = float(c["start"]), float(c["end"])
        if b - a > 0.05:
            removals.append((a, b))
            extra_rows.append({"start": a, "end": b, "reason": c.get("reason", "")})
    removals = merge_intervals(removals)

    # ---- 3) 保留段 ----
    keep = complement(removals, duration)
    if not keep:
        die("剪完什么都不剩——检查 plan / 阈值")

    # ---- 4) 钩子前置（整段移到开头；原位置剔除）----
    hook = plan.get("hook")
    hook_info = None
    if hook:
        hs, he = float(hook["start"]), float(hook["end"])
        if not (0 <= hs < he <= duration):
            die(f"钩子区间非法：{hs}–{he}")
        # 把 keep 在 hs/he 处切开，再分类
        pieces = []
        hook_pcs, rest_pcs = [], []
        for a, b in keep:
            cuts = sorted({a, b, max(a, min(b, hs)), max(a, min(b, he))})
            for i in range(len(cuts) - 1):
                seg = (cuts[i], cuts[i + 1])
                if seg[1] - seg[0] <= 0.02:
                    continue
                mid = (seg[0] + seg[1]) / 2
                (hook_pcs if hs <= mid < he else rest_pcs).append(seg)
        ordered = hook_pcs + rest_pcs
        hook_dur = sum(b - a for a, b in hook_pcs)
        hook_info = {"start": hs, "end": he, "text": hook.get("text", ""), "reason": hook.get("reason", ""),
                     "moved_seconds": round(hook_dur, 3)}
        log(f"钩子前置：「{hook.get('text','')}」{hs}–{he} → 开头（{hook_dur:.2f}s），原位置已剔除")
    else:
        ordered = list(keep)

    # ---- 5) 渲染粗剪片 ----
    fc, vlabels = [], []
    for i, (a, b) in enumerate(ordered):
        fc.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
        vlabels.append(f"[v{i}][a{i}]")
    fc.append("".join(vlabels) + f"concat=n={len(ordered)}:v=1:a=1[outv][outa]")
    out_mp4 = out / "cut.mp4"
    r = run(["ffmpeg", "-y", "-i", str(proxy), "-filter_complex", ";".join(fc),
             "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out_mp4)])
    if r.returncode != 0 or not out_mp4.is_file():
        die(f"合成失败：{(r.stderr or r.stdout or '')[-400:]}")
    new_dur = probe_duration(out_mp4)
    log(f"合成：{len(ordered)} 段 → {out_mp4.name}（{new_dur:.2f}s）")

    # ---- 6) 转录重映射（词级；被切开的长句按词边界拆条）----
    def map_point(t: float, piece: tuple[float, float], offset: float) -> float:
        a, b = piece
        return offset + max(0.0, min(t, b) - a)

    offsets, acc = [], 0.0
    for a, b in ordered:
        offsets.append(acc)
        acc += b - a

    new_segments = []
    for si, seg in enumerate(tr.get("segments", [])):
        words = seg.get("words") or []
        if not words:
            # 无词级信息：整段塞进所属保留片
            s, e = float(seg["start"]), float(seg["end"])
            for pi, (a, b) in enumerate(ordered):
                ia, ib = max(a, s), min(b, e)
                if ib - ia > 0.1:
                    new_segments.append({"start": round(map_point(ia, (a, b), offsets[pi]), 3),
                                         "end": round(map_point(ib, (a, b), offsets[pi]), 3),
                                         "text": seg.get("text", ""), "words": [], "_src": si})
            continue
        # 每个词归到相交最大的保留片
        assigned: dict[int, list] = {}
        for w in words:
            ws, we = float(w["start"]), float(w["end"])
            best, best_ov = None, 0.0
            for pi, (a, b) in enumerate(ordered):
                ov = min(we, b) - max(ws, a)
                if ov > best_ov:
                    best, best_ov = pi, ov
            if best is None or best_ov <= 0:
                continue
            a, b = ordered[best]
            nw = {"word": w.get("word", ""),
                  "start": round(map_point(ws, (a, b), offsets[best]), 3),
                  "end": round(map_point(we, (a, b), offsets[best]), 3)}
            assigned.setdefault(best, []).append(nw)
        for pi in sorted(assigned):
            ws_ = sorted(assigned[pi], key=lambda x: x["start"])
            if not ws_:
                continue
            new_segments.append({"start": ws_[0]["start"], "end": ws_[-1]["end"],
                                 "text": "".join(x["word"] for x in ws_), "words": ws_, "_src": si})
    new_segments.sort(key=lambda s: s["start"])

    # 同句碎片合并：同源段、且在时间轴上相邻（间隔 < 0.45s）的碎片合回一条字幕
    merged: list[dict] = []
    for frag in new_segments:
        if merged and merged[-1].get("_src") == frag.get("_src") and frag["start"] - merged[-1]["end"] < 0.45:
            merged[-1]["end"] = frag["end"]
            merged[-1]["text"] += frag["text"]
            merged[-1]["words"] += frag["words"]
        else:
            merged.append(dict(frag))
    new_segments = [{k: v for k, v in s.items() if k != "_src"} for s in merged]

    (out / "transcript.json").write_text(json.dumps(
        {"language": tr.get("language", "zh"), "duration": round(new_dur, 3),
         "segments": new_segments, "prep": {"cut_from": str(proxy), "hook": hook_info,
                                              "orig_duration": round(duration, 3), "new_duration": round(new_dur, 3)}},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 7) 对账 + 清单 ----
    kept_total = sum(b - a for a, b in ordered)
    report = {"orig_duration": round(duration, 3), "new_duration": round(new_dur, 3),
              "removed_total": round(sum(b - a for a, b in removals), 3),
              "kept_segments": [{"start": round(a, 3), "end": round(b, 3)} for a, b in ordered],
              "silences": sil_rows, "extra_cuts": extra_rows, "hook": hook_info,
              "accounting_ok": abs(kept_total - new_dur) < 0.25}
    (out / "cut-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# 粗剪清单（Step 0.5）", "",
             f"> 原时长 {duration:.2f}s → 新时长 {new_dur:.2f}s（收掉 {duration - new_dur:.2f}s）", ""]
    if hook_info:
        lines += ["## 钩子前置", f"- 「{hook_info['text']}」 {hook_info['start']}–{hook_info['end']}s → 开头（原位置已剔除，无重复画面）", ""]
    else:
        lines += ["## 钩子前置", "- 本片未前置（plan.hook = null）", ""]
    lines += ["## 剪掉的气口（-32dB / 0.7s → 留 0.22s 呼吸）", ""]
    if sil_rows:
        lines += ["| 位置(s) | 静音时长 | 剪掉 |", "|---|---|---|"]
        lines += [f"| {r['start']}–{r['end']} | {round(r['end'] - r['start'], 2)}s | {r['removed']}s |" for r in sil_rows]
    else:
        lines += ["（无）"]
    lines += ["", "## 额外删除（口误/重复）", ""]
    lines += [f"- {r['start']}–{r['end']}s：{r['reason']}" for r in extra_rows] or ["（无）"]
    lines += ["", "## 对账", f"- Σ保留段 {kept_total:.2f}s ≈ 新时长 {new_dur:.2f}s → {'OK' if report['accounting_ok'] else 'FAIL'}", ""]
    (out / "cut-list.md").write_text("\n".join(lines), encoding="utf-8")

    if not report["accounting_ok"]:
        die(f"对账不过：保留 {kept_total:.2f}s vs 新时长 {new_dur:.2f}s")
    log(f"完成：{out_mp4} · {out/'transcript.json'} · {out/'cut-list.md'}")


if __name__ == "__main__":
    main()
