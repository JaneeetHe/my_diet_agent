"""把数字整理成中文文本。"""
from __future__ import annotations

from datetime import date as Date, timedelta

from .parser import total


def r0(x: float) -> str:
    return f"{round(x) + 0:g}"


def r1(x: float) -> str:
    return f"{round(x, 1) + 0.0:g}"


def items_table(items) -> str:
    lines = ["| 项目 | 热量 | 蛋白 | 碳水 | 脂肪 |", "|---|---:|---:|---:|---:|"]
    for it in items:
        lines.append(f"| {it.describe()} | {r0(it.kcal)} | {r1(it.protein)} | {r1(it.carb)} | {r1(it.fat)} |")
    t = total(items)
    lines.append(f"| **合计** | **{r0(t['kcal'])}** | **{r1(t['protein'])}** | **{r1(t['carb'])}** | **{r1(t['fat'])}** |")
    formula = " + ".join(r0(it.kcal) for it in items).replace("+ -", "− ")
    lines.append(f"\n算式：{formula} = {r0(t['kcal'])} kcal")
    return "\n".join(lines)


def status(t: dict, cfg: dict) -> str:
    k, p = t["kcal"], t["protein"]
    lo, hi, rc = cfg["kcal_min"], cfg["kcal_max"], cfg["recharge_max"]
    if k < lo:
        ks = f"热量 {r0(k)} kcal，距目标区间还有 {r0(lo - k)}–{r0(hi - k)} kcal 空间"
    elif k <= hi:
        ks = f"热量 {r0(k)} kcal，已在目标区间 {lo}–{hi} 内"
    elif k <= rc:
        ks = f"热量 {r0(k)} kcal，超出目标 {r0(k - hi)}，在充能日范围内（≤{rc}）"
    else:
        ks = f"热量 {r0(k)} kcal，超出充能日上限 {r0(k - rc)}"
    pmin, pgoal = cfg["protein_min"], cfg["protein_goal"]
    if p < pmin:
        ps = f"蛋白质 {r1(p)} g，距底线 {pmin}g 还差 {r1(pmin - p)} g"
    elif p < pgoal:
        ps = f"蛋白质 {r1(p)} g，已过底线，距理想值 {pgoal}g 还差 {r1(pgoal - p)} g"
    else:
        ps = f"蛋白质 {r1(p)} g，已达理想值 ✓"
    return f"{ks}；{ps}。"


def archive_line(day: str, t: dict, note: str = "") -> str:
    return f"{day} | {r0(t['kcal'])} | {r1(t['protein'])} | {r1(t['carb'])} | {r1(t['fat'])} | {note}"


def day_report(day: str, rows, cfg: dict, note: str = "") -> str:
    if not rows:
        return f"{day} 还没有记录。"
    out = [f"## {day} 饮食记录"]
    meals: dict[str, list] = {}
    for r in rows:
        meals.setdefault(r["meal"] or "未分餐", []).append(r)
    for meal, rs in meals.items():
        mt = total(rs)
        out.append(f"\n**{meal}**（{r0(mt['kcal'])} kcal）")
        for r in rs:
            sign = "−" if r["qty"] < 0 else ""
            q = "" if abs(r["qty"]) == 1 else f" ×{abs(r['qty']):g}"
            tag = "" if r["source"] == "手册" else f"【{r['source']}】"
            out.append(f"- [#{r['id']}] {sign}{r['code'] or r['name']}{q}{tag}：{r0(r['kcal'])} kcal / {r1(r['protein'])}g 蛋白")
    t = total(rs for rs in rows)
    out.append("\n| 热量 | 蛋白 | 碳水 | 脂肪 |\n|---:|---:|---:|---:|")
    out.append(f"| {r0(t['kcal'])} | {r1(t['protein'])} | {r1(t['carb'])} | {r1(t['fat'])} |")
    out.append("\n" + status(t, cfg))
    out.append("\n存档：\n```\n" + archive_line(day, t, note) + "\n```")
    return "\n".join(out)


def week_report(end: str, day_totals, cfg: dict) -> str:
    end_d = Date.fromisoformat(end)
    start = (end_d - timedelta(days=6)).isoformat()
    rows = [r for r in day_totals if start <= r["date"] <= end]
    if not rows:
        return f"{start} 至 {end} 没有记录。"
    n = len(rows)
    avg = {k: sum(r[k] for r in rows) / n for k in ("kcal", "protein", "carb", "fat")}
    out = [f"## 周报 {start} 至 {end}（有记录 {n} 天）",
           "| 日期 | 热量 | 蛋白 | 碳水 | 脂肪 |", "|---|---:|---:|---:|---:|"]
    for r in rows:
        out.append(f"| {r['date']} | {r0(r['kcal'])} | {r1(r['protein'])} | {r1(r['carb'])} | {r1(r['fat'])} |")
    out.append(f"| **日均** | **{r0(avg['kcal'])}** | **{r1(avg['protein'])}** | **{r1(avg['carb'])}** | **{r1(avg['fat'])}** |")
    in_range = sum(1 for r in rows if cfg["kcal_min"] <= r["kcal"] <= cfg["kcal_max"])
    p_ok = sum(1 for r in rows if r["protein"] >= cfg["protein_min"])
    out.append(f"\n热量在 {cfg['kcal_min']}–{cfg['kcal_max']} 区间的天数：{in_range}/{n}；"
               f"蛋白质达到 {cfg['protein_min']}g 的天数：{p_ok}/{n}。")
    out.append(status(avg, cfg).replace("热量", "日均热量", 1).replace("蛋白质", "日均蛋白质", 1))
    return "\n".join(out)
