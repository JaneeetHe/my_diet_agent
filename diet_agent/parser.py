"""速记语法解析。

支持的写法（可混用，用 + 连接，- 表示减去）：
    早标A + 饼4 + 汤1*0.5
    汤2 + 8只虾 - 橄榄油 + 2勺辣酱
    半碗碗1、饼包×2
    外食健康餐(730kcal, 48g蛋白, 60g碳水, 25g脂肪)   ← 括号里的数值直接采用
代号里本身带 "-"（如 果-C、肉-虾），解析时会自动区分。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .foods import Food, FoodDB

UNITS = "个只勺块份包把片碗袋杯颗根盒瓶条锅"
NUM = r"\d+(?:\.\d+)?"
RE_MULT = re.compile(rf"^(.+?)\s*[*×xX]\s*({NUM})$")
RE_PREFIX = re.compile(rf"^({NUM})\s*([{UNITS}])?\s*(.+)$")
RE_TRAIL = re.compile(rf"^(.+?)({NUM})$")
RE_CUSTOM = re.compile(r"^(.+?)\s*[（(](.+)[）)]$")


@dataclass
class Item:
    code: str | None
    name: str
    qty: float
    kcal: float
    protein: float
    carb: float
    fat: float
    source: str  # 手册 / 自报 / 估算
    raw: str

    def describe(self) -> str:
        q = self.qty
        sign = "−" if q < 0 else ""
        q = abs(q)
        qs = "" if q == 1 else f" ×{q:g}"
        tag = "" if self.source == "手册" else f"【{self.source}】"
        label = self.code or self.name
        return f"{sign}{label}{qs}{tag}"


class ParseError(ValueError):
    def __init__(self, unknown: list[str]):
        self.unknown = unknown
        super().__init__("无法识别：" + "、".join(unknown))


def _from_food(f: Food, qty: float, raw: str) -> Item:
    return Item(f.code, f.name, qty, f.kcal * qty, f.protein * qty,
                f.carb * qty, f.fat * qty, "手册", raw)


def _parse_custom_values(s: str) -> dict | None:
    def grab(pattern: str) -> float | None:
        m = re.search(pattern, s, re.I)
        return float(m.group(1)) if m else None

    kcal = grab(rf"({NUM})\s*(?:kcal|大卡|千卡|卡)")
    if kcal is None:
        return None
    return {
        "kcal": kcal,
        "protein": grab(rf"({NUM})\s*g?\s*蛋白") or grab(rf"蛋白质?\s*({NUM})") or 0.0,
        "carb": grab(rf"({NUM})\s*g?\s*碳水") or grab(rf"碳水\s*({NUM})") or 0.0,
        "fat": grab(rf"({NUM})\s*g?\s*脂肪") or grab(rf"脂肪\s*({NUM})") or 0.0,
    }


def parse_term(term: str, db: FoodDB) -> Item:
    raw = term.strip()
    t = raw
    if not t:
        raise ParseError([raw])

    # 1) 括号自报数值：名称(730kcal, 48g蛋白)
    m = RE_CUSTOM.match(t)
    if m:
        vals = _parse_custom_values(m.group(2))
        if vals is not None:
            return Item(None, m.group(1).strip(), 1, vals["kcal"], vals["protein"],
                        vals["carb"], vals["fat"], "自报", raw)

    qty = 1.0
    # 2) 后缀倍数：汤1*0.5
    m = RE_MULT.match(t)
    if m:
        t, qty = m.group(1).strip(), float(m.group(2))

    # 3) "半"开头：半碗碗1 / 半个汤1
    if t.startswith("半"):
        qty *= 0.5
        t = t[1:]
        if t and t[0] in UNITS and not db.get(t):
            t = t[1:]

    # 4) 直接命中代号/别名
    f = db.get(t)
    if f:
        return _from_food(f, qty, raw)

    # 5) 数量前缀：8只虾、2勺辣酱
    m = RE_PREFIX.match(t)
    if m:
        f = db.get(m.group(3))
        if f:
            n = float(m.group(1))
            return _from_food(f, qty * n / f.per, raw)

    # 6) 尾部数字：饼4
    m = RE_TRAIL.match(t)
    if m:
        f = db.get(m.group(1))
        if f:
            return _from_food(f, qty * float(m.group(2)), raw)

    raise ParseError([raw])


def _split_top(text: str, seps: str) -> list[str]:
    """在括号外按分隔符切分。"""
    parts, buf, depth = [], [], 0
    for ch in text:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth = max(0, depth - 1)
        if ch in seps and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def _parse_part(part: str, db: FoodDB) -> list[Item]:
    """处理一段可能含 '-' 的文本；'-' 既可能是减号，也可能是代号的一部分。"""
    stripped = part.strip()
    if not stripped:
        return []
    negate_first = stripped.startswith("-")
    segs = _split_top(stripped[1:] if negate_first else stripped, "-")

    memo: dict[int, list[Item] | None] = {}

    def solve(i: int) -> list[Item] | None:
        if i == len(segs):
            return []
        if i in memo:
            return memo[i]
        for j in range(len(segs), i, -1):  # 优先最长匹配
            chunk = "-".join(segs[i:j]).strip()
            if not chunk:
                continue
            try:
                item = parse_term(chunk, db)
            except ParseError:
                continue
            rest = solve(j)
            if rest is not None:
                memo[i] = [item] + rest
                return memo[i]
        memo[i] = None
        return None

    items = solve(0)
    if items is None:
        raise ParseError([stripped])
    for k, it in enumerate(items):
        if k > 0 or negate_first:
            it.qty, it.kcal, it.protein, it.carb, it.fat = (
                -it.qty, -it.kcal, -it.protein, -it.carb, -it.fat)
    return items


def parse(text: str, db: FoodDB) -> list[Item]:
    db.refresh_if_changed()
    norm = (text.replace("＋", "+").replace("－", "-").replace("—", "-")
            .replace("−", "-").replace("＊", "*"))
    items: list[Item] = []
    unknown: list[str] = []
    for part in _split_top(norm, "+,，、;；\n"):
        try:
            items.extend(_parse_part(part, db))
        except ParseError as e:
            unknown.extend(e.unknown)
    if unknown:
        raise ParseError(unknown)
    return items


def total(items) -> dict:
    t = {"kcal": 0.0, "protein": 0.0, "carb": 0.0, "fat": 0.0}
    for it in items:
        for k in t:
            t[k] += getattr(it, k) if hasattr(it, k) else it[k]
    return t
