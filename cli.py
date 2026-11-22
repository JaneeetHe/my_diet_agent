"""命令行版本，不经过 Claude 也能用。

  python cli.py calc "早标A + 饼4 + 汤1"      只计算
  python cli.py log  "早标A + 饼包" 早餐      记录（餐次可省略）
  python cli.py today                         今日汇总
  python cli.py week                          最近 7 天
  python cli.py del 12                        删除 #12
  python cli.py foods                         食物库
  python cli.py chart 30                      最近 30 天趋势图（默认 7）
"""
import sys

# Windows 终端默认 GBK，统一用 UTF-8 输出中文和符号
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import server


def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    if cmd == "calc":
        print(server.log_food(args[0], dry_run=True))
    elif cmd == "log":
        print(server.log_food(args[0], meal=args[1] if len(args) > 1 else ""))
    elif cmd == "today":
        print(server.day_summary(args[0] if args else ""))
    elif cmd == "week":
        print(server.weekly_report(args[0] if args else ""))
    elif cmd == "del":
        print(server.delete_entry(int(args[0])))
    elif cmd == "chart":
        print(server.trend_chart(int(args[0]) if args else 7))
    elif cmd == "foods":
        print(server.list_foods())
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
