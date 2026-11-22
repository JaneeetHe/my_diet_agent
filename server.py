"""减脂饮食管家 —— MCP 服务器（在 Claude Desktop 中使用）。"""
from __future__ import annotations

import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Server

from diet_agent import db as store
from diet_agent.foods import FoodDB, load_config
from diet_agent.parser import Item, ParseError, parse
from diet_agent.report import day_report, items_table, status, total, week_report

INSTRUCTIONS = """你是我的减脂饮食管家。所有数字都由工具计算，不要自己心算或凭记忆给数值。
- 我报饮食时，把原话（保留代号）传给 log_food。能看出餐次就填 meal（早餐/午餐/晚餐/加餐）。
- log_food 报"无法识别"时：先 list_foods 看有没有对应代号；确实没有，就按标准营养数据估算，用 log_custom 记录（estimated=true），并告诉我估算值。
- 每次记录后，根据工具返回的状态，用一两句话告诉我还剩多少空间、蛋白质够不够，给下一餐的简短建议。
- 我说"收官"时调用 day_summary，简短总结今天（先肯定做得好的，不制造焦虑），并原样给出存档行。
- 我说要新增常吃的食物时，用 add_food 存进食物库。
"""

mcp = Server("减脂饮食管家", instructions=INSTRUCTIONS)
foods = FoodDB()
conn = store.connect()


def _day(d: str) -> str:
    return d.strip() or Date.today().isoformat()


@mcp.tool()
def log_food(text: str, meal: str = "", date: str = "", dry_run: bool = False) -> str:
    """记录一餐（用速记语法）。
    text 示例："早标A + 饼4 + 汤1*0.5"、"汤2 + 8只虾 - 橄榄油 + 2勺辣酱"、"外食(730kcal, 48g蛋白)"。
    meal：早餐/午餐/晚餐/加餐，可留空。date：YYYY-MM-DD，留空为今天。
    dry_run=true 只计算不保存。任何一项无法识别时整条都不会保存。"""
    day = _day(date)
    try:
        items = parse(text, foods)
    except ParseError as e:
        return (f"无法识别：{'、'.join(e.unknown)}。本条未保存。"
                "请检查代号，或用 log_custom 估算录入未知食物。")
    out = [items_table(items)]
    if dry_run:
        out.insert(0, "（试算，未保存）")
        return "\n".join(out)
    ids = store.add_items(conn, day, meal, items)
    day_total = total(store.day_rows(conn, day))
    out.insert(0, f"已记录到 {day} {meal}（编号 #{ids[0]}–#{ids[-1]}）")
    out.append(f"\n今日累计：{status(day_total, load_config())}")
    return "\n".join(out)


@mcp.tool()
def log_custom(name: str, kcal: float, protein: float = 0, carb: float = 0, fat: float = 0,
               meal: str = "", date: str = "", estimated: bool = True) -> str:
    """记录食物库里没有的东西。estimated=true 表示是估算值，false 表示包装/外食标注值。"""
    day = _day(date)
    item = Item(None, name, 1, kcal, protein, carb, fat, "估算" if estimated else "自报", name)
    store.add_items(conn, day, meal, [item])
    return (f"已记录 {name}：{kcal:g} kcal / {protein:g}g 蛋白【{item.source}】\n"
            f"今日累计：{status(total(store.day_rows(conn, day)), load_config())}")


@mcp.tool()
def day_summary(date: str = "", note: str = "") -> str:
    """查看某天（默认今天）的明细、合计、目标状态和存档行。note 会写进存档行的备注栏。"""
    day = _day(date)
    if note:
        store.set_note(conn, day, note)
    return day_report(day, store.day_rows(conn, day), load_config(), store.get_note(conn, day))


@mcp.tool()
def weekly_report(end_date: str = "") -> str:
    """最近 7 天（截至 end_date，默认今天）每日数据与日均。"""
    end = _day(end_date)
    start = (Date.fromisoformat(end).toordinal() - 6)
    start = Date.fromordinal(start).isoformat()
    return week_report(end, store.range_totals(conn, start, end), load_config())


@mcp.tool()
def delete_entry(entry_id: int) -> str:
    """按编号删除一条记录（编号见 day_summary 里的 #数字）。"""
    row = store.delete(conn, entry_id)
    if not row:
        return f"没有编号 #{entry_id} 的记录。"
    return f"已删除 #{entry_id}：{row['date']} {row['code'] or row['name']}（{row['kcal']:.0f} kcal）"


@mcp.tool()
def list_foods() -> str:
    """列出食物库里所有代号和每份营养。"""
    foods.refresh_if_changed()
    lines = ["| 代号 | 名称 | 份量 | 热量 | 蛋白 | 碳水 | 脂肪 | 别名 |", "|---|---|---|---:|---:|---:|---:|---|"]
    for f in foods.foods.values():
        lines.append(f"| {f.code} | {f.name} | {f.portion} | {f.kcal:g} | {f.protein:g} | {f.carb:g} | {f.fat:g} | {'、'.join(f.aliases)} |")
    return "\n".join(lines)


@mcp.tool()
def add_food(code: str, name: str, portion: str, kcal: float, protein: float, carb: float,
             fat: float, aliases: list[str] | None = None, per: float = 1) -> str:
    """往食物库新增一个代号（按 1 份计）。per：1 份等于几个单位，例如 8只虾 一份就填 8。"""
    try:
        f = foods.add(code, name, portion, kcal, protein, carb, fat, aliases, per)
    except ValueError as e:
        return str(e)
    return f"已新增 {f.code}（{f.name}，{f.portion}）：{f.kcal:g} kcal / {f.protein:g}g 蛋白"


if __name__ == "__main__":
    mcp.run()
