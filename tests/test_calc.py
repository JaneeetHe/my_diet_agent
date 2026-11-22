import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from diet_agent.foods import FoodDB  # noqa: E402
from diet_agent.parser import ParseError, parse, total  # noqa: E402

db = FoodDB(ROOT / "foods.yaml")


def kcal(text):
    return round(total(parse(text, db))["kcal"], 1)


@pytest.mark.parametrize("text,expected", [
    ("早标A + 饼4 + 汤1 + 果-C", 970),                               # 手册示例1
    ("早标B + 碗2 + 碗1 + 肉-鸡胸 + 2勺辣酱 + 果-H", 990),            # 手册示例2
    ("早标B + 汤2 + 西红柿 + 辣酱 + 果-C + 饮-L", 655),               # 手册示例3
    ("早标A + 饼包 + 碗2", 365),                                     # 手册示例4
    ("汤1*0.5", 262.5),
    ("汤1 - 土豆", 410),
    ("汤1-土豆-虾", 325),
    ("汤2 + 8只虾 - 橄榄油", 335),
    ("汤2 + 4只虾", 382.5),
    ("饼包×2", 300),
    ("半碗碗1", 177.5),
    ("果-C、果-K，果-莓", 180),
    ("外食健康餐(730kcal, 48g蛋白)", 730),
    ("-油1", -90),
])
def test_kcal(text, expected):
    assert kcal(text) == expected


def test_custom_macros():
    t = total(parse("外食(730kcal, 48g蛋白, 60g碳水, 25g脂肪)", db))
    assert (t["protein"], t["carb"], t["fat"]) == (48, 60, 25)


def test_unknown_reported():
    with pytest.raises(ParseError) as e:
        parse("早标A + 披萨 + 饼4", db)
    assert e.value.unknown == ["披萨"]
