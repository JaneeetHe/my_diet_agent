"""生成趋势图（单个 HTML 文件，离线可看，浏览器打开）。"""
from __future__ import annotations

import json
from datetime import date as Date, timedelta
from pathlib import Path

from .foods import ROOT

REPORT_DIR = ROOT / "reports"


def build_series(day_totals, end: str, days: int) -> list[dict]:
    end_d = Date.fromisoformat(end)
    by_date = {r["date"]: r for r in day_totals}
    out = []
    for i in range(days - 1, -1, -1):
        d = (end_d - timedelta(days=i)).isoformat()
        r = by_date.get(d)
        out.append({
            "date": d,
            "kcal": round(r["kcal"]) if r else None,
            "protein": round(r["protein"], 1) if r else None,
            "carb": round(r["carb"], 1) if r else None,
            "fat": round(r["fat"], 1) if r else None,
        })
    # 7 日滚动平均（含窗口之前的数据，只计有记录的天）
    for p in out:
        d0 = Date.fromisoformat(p["date"])
        win = [by_date[k]["kcal"] for k in ((d0 - timedelta(days=j)).isoformat() for j in range(7)) if k in by_date]
        p["kcal_avg7"] = round(sum(win) / len(win)) if (win and p["kcal"] is not None) else None
    return out


def render(series: list[dict], cfg: dict, title: str) -> str:
    payload = json.dumps({"series": series, "cfg": cfg, "title": title}, ensure_ascii=False)
    return HTML.replace("__DATA__", payload).replace("__TITLE__", title)


def write_report(day_totals, end: str, days: int, cfg: dict) -> Path:
    series = build_series(day_totals, end, days)
    start = series[0]["date"]
    title = f"饮食趋势 {start} 至 {end}（{days} 天）"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"trend_{end}_{days}d.html"
    path.write_text(render(series, cfg, title), encoding="utf-8")
    return path


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
.viz-root{color-scheme:light;
  --surface-0:#f4f3f0;--surface-1:#fcfcfb;--border:#e4e2dc;--grid:#ecebe7;
  --text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#8a8985;
  --series-1:#2a78d6;--series-2:#eb6834;--series-3:#1baf7a;--band:rgba(27,175,122,.10);}
@media (prefers-color-scheme:dark){.viz-root{color-scheme:dark;
  --surface-0:#121211;--surface-1:#1a1a19;--border:#2e2e2c;--grid:#262624;
  --text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#8f8e88;
  --series-1:#3987e5;--series-2:#d95926;--series-3:#199e70;--band:rgba(25,158,112,.16);}}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 system-ui,"Microsoft YaHei","PingFang SC",sans-serif}
.viz-root{background:var(--surface-0);color:var(--text-primary);min-height:100vh;padding:28px 20px}
.wrap{max-width:960px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--text-secondary);margin:0 0 20px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px 16px}
.tile .k{color:var(--text-secondary);font-size:13px}
.tile .v{font-size:26px;font-weight:600;font-variant-numeric:tabular-nums}
.tile .n{color:var(--text-muted);font-size:12px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:16px 16px 8px;margin-bottom:16px;position:relative}
.card h2{font-size:15px;margin:0}
.card .note{color:var(--text-secondary);font-size:12px;margin:2px 0 6px}
.legend{display:flex;gap:16px;flex-wrap:wrap;color:var(--text-secondary);font-size:12px;margin:4px 0 4px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-2px}
.legend i.line{height:2px;border-radius:1px;vertical-align:3px}
.legend i.band{background:var(--band);border:1px dashed var(--series-3)}
svg{width:100%;height:auto;display:block}
.axis text{fill:var(--text-muted);font-size:11px}
.grid line{stroke:var(--grid)}
.ref{stroke:var(--text-muted);stroke-dasharray:4 4;stroke-width:1}
.reflabel{fill:var(--text-secondary);font-size:11px}
.tip{position:absolute;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);
  border-radius:8px;padding:8px 10px;font-size:12px;box-shadow:0 4px 14px rgba(0,0,0,.12);display:none;white-space:nowrap}
.tip b{display:block;margin-bottom:2px}
.tip .sw{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px}
details{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:12px 16px}
summary{cursor:pointer;color:var(--text-secondary)}
table{border-collapse:collapse;width:100%;margin-top:10px;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;border-bottom:1px solid var(--grid);text-align:right}
th:first-child,td:first-child{text-align:left}
th{color:var(--text-secondary);font-weight:500}
</style></head>
<body><div class="viz-root"><div class="wrap">
<h1 id="title"></h1><p class="sub" id="sub"></p>
<div class="tiles" id="tiles"></div>

<div class="card" id="c-kcal"><h2>每日热量</h2>
<div class="note" id="kcal-note"></div>
<div class="legend"><span><i style="background:var(--series-1)"></i>每日热量</span>
<span><i class="line" style="background:var(--series-2)"></i>7 日平均</span>
<span><i class="band"></i>目标区间</span></div>
<svg viewBox="0 0 900 280" id="s-kcal" role="img" aria-label="每日热量柱状图"></svg><div class="tip"></div></div>

<div class="card" id="c-pro"><h2>每日蛋白质</h2>
<div class="note" id="pro-note"></div>
<svg viewBox="0 0 900 240" id="s-pro" role="img" aria-label="每日蛋白质柱状图"></svg><div class="tip"></div></div>

<div class="card" id="c-mac"><h2>热量来源（蛋白质 / 碳水 / 脂肪）</h2>
<div class="note">按 蛋白质×4、碳水×4、脂肪×9 换算成 kcal</div>
<div class="legend"><span><i style="background:var(--series-1)"></i>蛋白质</span>
<span><i style="background:var(--series-2)"></i>碳水</span>
<span><i style="background:var(--series-3)"></i>脂肪</span></div>
<svg viewBox="0 0 900 260" id="s-mac" role="img" aria-label="热量来源堆叠柱状图"></svg><div class="tip"></div></div>

<details><summary>查看数据表</summary><table id="tbl"></table></details>
</div></div>
<script>
const D = __DATA__;
const S = D.series, C = D.cfg;
const NS = "http://www.w3.org/2000/svg";
const logged = S.filter(d => d.kcal !== null);
const avg = k => logged.length ? logged.reduce((a, d) => a + d[k], 0) / logged.length : null;
const fmtD = s => s.slice(5).replace("-", "/");
const wk = s => "日一二三四五六"[new Date(s + "T00:00:00").getDay()];

document.getElementById("title").textContent = D.title;
document.getElementById("sub").textContent =
  `有记录 ${logged.length} / ${S.length} 天 · 目标 ${C.kcal_min}–${C.kcal_max} kcal，蛋白质 ≥ ${C.protein_min} g`;

const inRange = logged.filter(d => d.kcal >= C.kcal_min && d.kcal <= C.kcal_max).length;
const pOk = logged.filter(d => d.protein >= C.protein_min).length;
const ak = avg("kcal"), ap = avg("protein");
const tiles = [
  ["日均热量", ak === null ? "—" : Math.round(ak) + " kcal", `目标 ${C.kcal_min}–${C.kcal_max}`],
  ["日均蛋白质", ap === null ? "—" : ap.toFixed(1) + " g", `底线 ${C.protein_min} g · 理想 ${C.protein_goal} g`],
  ["热量在区间内", `${inRange} / ${logged.length} 天`, "有记录的天数中"],
  ["蛋白质达标", `${pOk} / ${logged.length} 天`, `≥ ${C.protein_min} g`],
];
document.getElementById("tiles").innerHTML = tiles.map(t =>
  `<div class="tile"><div class="k">${t[0]}</div><div class="v">${t[1]}</div><div class="n">${t[2]}</div></div>`).join("");
document.getElementById("kcal-note").textContent = logged.length < S.length ? "空白的日期表示当天没有记录" : "";
document.getElementById("pro-note").textContent = `虚线：底线 ${C.protein_min} g，理想 ${C.protein_goal} g`;

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function niceMax(v) { const s = [100, 200, 250, 500, 1000]; for (const x of s) if (v / x <= 6) return Math.ceil(v / x) * x; return Math.ceil(v / 1000) * 1000; }

// 通用：柱状（可堆叠）+ 可选折线 + 参考线/区间 + 悬停
function chart(svgId, opt) {
  const svg = document.getElementById(svgId), card = svg.parentNode, tip = card.querySelector(".tip");
  const VB = svg.viewBox.baseVal, W = VB.width, H = VB.height;
  const m = {l: 48, r: 56, t: 12, b: 34}, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = S.length, step = iw / n, bw = Math.max(3, Math.min(28, step * 0.62));
  const yMax = niceMax(opt.max);
  const y = v => m.t + ih - (v / yMax) * ih;
  const xc = i => m.l + step * (i + 0.5);

  const g = el("g", {class: "grid"}, svg), ax = el("g", {class: "axis"}, svg);
  const ticks = 5;
  for (let k = 0; k <= ticks; k++) {
    const v = yMax / ticks * k;
    el("line", {x1: m.l, x2: W - m.r, y1: y(v), y2: y(v)}, g);
    el("text", {x: m.l - 8, y: y(v) + 4, "text-anchor": "end"}, ax).textContent = v;
  }
  if (opt.band) el("rect", {x: m.l, width: iw, y: y(opt.band[1]), height: y(opt.band[0]) - y(opt.band[1]), fill: "var(--band)"}, svg);
  (opt.refs || []).forEach(r => {
    el("line", {class: "ref", x1: m.l, x2: W - m.r, y1: y(r.v), y2: y(r.v)}, svg);
    el("text", {class: "reflabel", x: W - m.r + 6, y: y(r.v) + 4}, svg).textContent = r.label;
  });
  const every = Math.ceil(n / 12);
  S.forEach((d, i) => {
    if (i % every === 0 || i === n - 1)
      el("text", {x: xc(i), y: H - m.b + 18, "text-anchor": "middle"}, ax).textContent = n <= 14 ? `${fmtD(d.date)} ${wk(d.date)}` : fmtD(d.date);
  });

  // 柱：圆角只在顶端，段间 2px 间隙
  S.forEach((d, i) => {
    let base = 0;
    const parts = opt.stack(d);
    parts.forEach((p, j) => {
      if (p.v === null || p.v <= 0) return;
      const top = j === parts.length - 1;
      const y0 = y(base), y1 = y(base + p.v) + (j > 0 ? 2 : 0);
      const h = Math.max(0, y0 - y1), x0 = xc(i) - bw / 2, r = top ? Math.min(4, h, bw / 2) : 0;
      const path = `M${x0},${y0} V${y1 + r} Q${x0},${y1} ${x0 + r},${y1} H${x0 + bw - r} Q${x0 + bw},${y1} ${x0 + bw},${y1 + r} V${y0} Z`;
      el("path", {d: path, fill: p.color}, svg);
      base += p.v;
    });
  });
  if (opt.line) {
    let dstr = "", pen = false;
    S.forEach((d, i) => { const v = opt.line(d); if (v === null) { pen = false; return; }
      dstr += (pen ? "L" : "M") + xc(i) + "," + y(v); pen = true; });
    el("path", {d: dstr, fill: "none", stroke: "var(--series-2)", "stroke-width": 2, "stroke-linejoin": "round"}, svg);
  }
  // 悬停
  const cross = el("line", {y1: m.t, y2: m.t + ih, stroke: "var(--text-muted)", "stroke-width": 1, opacity: 0}, svg);
  const hit = el("rect", {x: m.l, y: m.t, width: iw, height: ih, fill: "transparent"}, svg);
  hit.addEventListener("mousemove", ev => {
    const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    const i = Math.max(0, Math.min(n - 1, Math.floor((p.x - m.l) / step)));
    const d = S[i];
    cross.setAttribute("x1", xc(i)); cross.setAttribute("x2", xc(i)); cross.setAttribute("opacity", .5);
    tip.innerHTML = `<b>${d.date}（周${wk(d.date)}）</b>` + opt.tip(d);
    tip.style.display = "block";
    const r = card.getBoundingClientRect(), tx = ev.clientX - r.left + 14;
    tip.style.left = Math.min(tx, r.width - tip.offsetWidth - 8) + "px";
    tip.style.top = (ev.clientY - r.top + 12) + "px";
  });
  hit.addEventListener("mouseleave", () => { tip.style.display = "none"; cross.setAttribute("opacity", 0); });
}
const sw = c => `<span class="sw" style="background:${c}"></span>`;
const none = "<span style='color:var(--text-muted)'>没有记录</span>";

chart("s-kcal", {
  max: Math.max(C.recharge_max, ...logged.map(d => d.kcal)),
  band: [C.kcal_min, C.kcal_max],
  refs: [{v: C.recharge_max, label: "充能上限"}],
  stack: d => [{v: d.kcal, color: "var(--series-1)"}],
  line: d => d.kcal_avg7,
  tip: d => d.kcal === null ? none :
    `${sw("var(--series-1)")}热量 ${d.kcal} kcal<br>${sw("var(--series-2)")}7 日平均 ${d.kcal_avg7} kcal`,
});
chart("s-pro", {
  max: Math.max(C.protein_goal * 1.2, ...logged.map(d => d.protein)),
  refs: [{v: C.protein_min, label: "底线"}, {v: C.protein_goal, label: "理想"}],
  stack: d => [{v: d.protein, color: "var(--series-1)"}],
  tip: d => d.protein === null ? none : `${sw("var(--series-1)")}蛋白质 ${d.protein} g`,
});
chart("s-mac", {
  max: Math.max(C.recharge_max, ...logged.map(d => d.protein * 4 + d.carb * 4 + d.fat * 9)),
  stack: d => d.kcal === null ? [] : [
    {v: d.protein * 4, color: "var(--series-1)"}, {v: d.carb * 4, color: "var(--series-2)"}, {v: d.fat * 9, color: "var(--series-3)"}],
  tip: d => {
    if (d.kcal === null) return none;
    const p = d.protein * 4, c = d.carb * 4, f = d.fat * 9, t = p + c + f || 1, pc = v => Math.round(v / t * 100);
    return `${sw("var(--series-1)")}蛋白质 ${d.protein} g（${pc(p)}%）<br>${sw("var(--series-2)")}碳水 ${d.carb} g（${pc(c)}%）<br>${sw("var(--series-3)")}脂肪 ${d.fat} g（${pc(f)}%）`;
  },
});

document.getElementById("tbl").innerHTML =
  "<tr><th>日期</th><th>热量 kcal</th><th>7 日平均</th><th>蛋白质 g</th><th>碳水 g</th><th>脂肪 g</th></tr>" +
  S.map(d => `<tr><td>${d.date} 周${wk(d.date)}</td>` +
    ["kcal", "kcal_avg7", "protein", "carb", "fat"].map(k => `<td>${d[k] ?? "—"}</td>`).join("") + "</tr>").join("");
</script></body></html>
"""
