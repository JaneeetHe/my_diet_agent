"""食物库：读取 foods.yaml，按代号或别名查找。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FOODS_PATH = Path(os.environ.get("DIET_FOODS", ROOT / "foods.yaml"))
CONFIG_PATH = Path(os.environ.get("DIET_CONFIG", ROOT / "config.yaml"))


def normalize(s: str) -> str:
    return s.strip().replace(" ", "").replace("　", "").lower()


@dataclass
class Food:
    code: str
    name: str
    portion: str
    kcal: float
    protein: float
    carb: float
    fat: float
    per: float = 1
    aliases: list[str] = field(default_factory=list)


class FoodDB:
    def __init__(self, path: Path | str = FOODS_PATH):
        self.path = Path(path)
        self._mtime = None
        self.reload()

    def reload(self) -> None:
        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        self.foods: dict[str, Food] = {}
        self.index: dict[str, Food] = {}
        for code, d in data.items():
            code = str(code)
            f = Food(
                code=code,
                name=str(d.get("name", code)),
                portion=str(d.get("portion", "1份")),
                kcal=float(d.get("kcal", 0)),
                protein=float(d.get("protein", 0)),
                carb=float(d.get("carb", 0)),
                fat=float(d.get("fat", 0)),
                per=float(d.get("per", 1) or 1),
                aliases=[str(a) for a in (d.get("aliases") or [])],
            )
            self.foods[code] = f
        # 代号优先于别名
        for f in self.foods.values():
            for a in f.aliases:
                self.index.setdefault(normalize(a), f)
        for f in self.foods.values():
            self.index[normalize(f.code)] = f
        self._mtime = self.path.stat().st_mtime

    def refresh_if_changed(self) -> None:
        if self.path.stat().st_mtime != self._mtime:
            self.reload()

    def get(self, name: str) -> Food | None:
        return self.index.get(normalize(name))

    def add(self, code: str, name: str, portion: str, kcal: float, protein: float,
            carb: float, fat: float, aliases: list[str] | None = None, per: float = 1) -> Food:
        """追加到 foods.yaml 末尾（保留原文件注释）。代号已存在则报错。"""
        self.refresh_if_changed()
        if code in self.foods:
            raise ValueError(f"代号「{code}」已存在，如需修改请直接编辑 foods.yaml")
        entry = {code: {"name": name, "portion": portion, "kcal": kcal,
                        "protein": protein, "carb": carb, "fat": fat}}
        if per and per != 1:
            entry[code]["per"] = per
        if aliases:
            entry[code]["aliases"] = list(aliases)
        text = yaml.safe_dump(entry, allow_unicode=True, sort_keys=False)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + text)
        self.reload()
        return self.foods[code]


def load_config() -> dict:
    defaults = {"kcal_min": 1300, "kcal_max": 1400, "recharge_max": 1600,
                "protein_min": 75, "protein_goal": 100}
    if CONFIG_PATH.exists():
        defaults.update(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {})
    return defaults
