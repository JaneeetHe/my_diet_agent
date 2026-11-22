# 减脂饮食管家（自用版）

在 Claude Code 里像平时一样说话："早标A + 饼包"、"汤2 + 8只虾 - 橄榄油"。
Claude 负责听懂，**计算和存档全部由本地代码完成**——不会算错，数据跨对话保留在你电脑上，还能画出一周 / 一个月的趋势图。

## 一次性安装（Windows）

以下命令都在 **VS Code 的 PowerShell 终端**里运行。

### 1. 安装 Python
到 python.org 下载 Python 3.12 或更新版本。安装时**务必勾选「Add python.exe to PATH」**。
装好后在终端输入 `py --version`，能看到版本号就行。

### 2. 进入项目文件夹并安装依赖

```powershell
cd C:\Users\你的用户名\Documents\MY_PROJECT\diet-agent
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. 自测

```powershell
.venv\Scripts\python -m pytest -q tests
.venv\Scripts\python cli.py calc "早标A + 饼4 + 汤1 + 果-C"
```

第一行应显示 `16 passed`，第二行应算出 970 kcal。

## 接入 Claude Code（VS Code）

> Claude Desktop 新版的普通对话在云端运行，不会加载电脑上的本地工具，所以用 VS Code 里的 Claude Code。

### 1. 在项目文件夹里创建 `.mcp.json`

把路径换成你自己的，然后运行：

```powershell
@'
{
  "mcpServers": {
    "diet": {
      "command": "C:\\Users\\你的用户名\\Documents\\MY_PROJECT\\diet-agent\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\你的用户名\\Documents\\MY_PROJECT\\diet-agent\\server.py"]
    }
  }
}
'@ | Set-Content -Encoding ascii .mcp.json
```

### 2. 启用
1. 用 VS Code 打开 `diet-agent` 文件夹。
2. 点右下角状态栏的 **Claude Code** 打开面板，新建会话。
3. 弹出是否启用 `diet` 服务器时选允许。
4. 发送 `早餐：早标A + 饼包`，看到它调用 `log_food` 并返回「已记录到…」就成功了。

### 改了代码之后
在 Claude Code 输入 `/mcp` → 选 diet → 重连；或按 `Ctrl + Shift + P` → `Reload Window`。

## 日常使用

直接对 Claude 说：

| 你说 | 发生什么 |
|---|---|
| `早餐：早标A + 饼包` | 记录并告诉你今天还剩多少 |
| `午餐 汤1*0.5 + 肉-鸡胸` | 喝了半锅汤 |
| `汤2 + 8只虾 - 橄榄油 + 2勺辣酱` | 临时加减 |
| `外食健康餐(730kcal, 48g蛋白)` | 直接采用你报的数 |
| `吃了一块披萨` | 库里没有 → Claude 估算后记录，标【估算】 |
| `看看今天的记录` | 今日明细（每条带 `#编号`） |
| `删掉 #5` / `把 #3 到 #6 都删了` | 删除记错的条目（删除后无法恢复） |
| `收官` | 今日明细 + 存档行 |
| `这周怎么样` | 最近 7 天每日数据和日均（文字版） |
| `看看这周的趋势` / `画最近 30 天` | 生成趋势图并在浏览器打开 |
| `把 XX 加进食物库，每份 … kcal` | 新增代号 |

记错了数量（比如汤只喝了一半）：先删掉那条，再重新记 `汤1*0.5`。

## 趋势图

一个离线可看的网页，包含：

- **汇总**：日均热量、日均蛋白质、热量在目标区间的天数、蛋白质达标天数
- **每日热量**：柱状图 + 7 日平均线，绿色带为目标区间，虚线为充能日上限
- **每日蛋白质**：柱状图，虚线为底线和理想值
- **热量来源**：每天的热量按 蛋白质×4 / 碳水×4 / 脂肪×9 拆成三段
- 鼠标悬停看当天数值；页面底部可展开完整数据表；跟随系统深色模式

没有记录的日子留空，不计入平均。图表保存在 `reports\` 文件夹。

## 命令行（不经过 Claude 也能用）

```powershell
.venv\Scripts\python cli.py calc "早标A + 饼4 + 汤1"   # 只计算，不保存
.venv\Scripts\python cli.py log  "早标A + 饼包" 早餐   # 记录（餐次可省略）
.venv\Scripts\python cli.py today                      # 今日汇总（含编号）
.venv\Scripts\python cli.py week                       # 最近 7 天（文字）
.venv\Scripts\python cli.py chart 30                   # 最近 30 天趋势图（默认 7）
.venv\Scripts\python cli.py del 12                     # 删除 #12
.venv\Scripts\python cli.py foods                      # 查看食物库
```

## 速记语法

- `+` 连接，`-` 减去（代号里自带的 `-` 如 `果-C` 会自动识别）；`、` `，` 也当作 `+`
- `饼4` = 4 块；`饼包` = 1 整包；`汤1*0.5` 或 `汤1×0.5` = 半份；`半碗碗1` = 半份
- `8只虾`：按"一份 = 8 只"折算（`foods.yaml` 里的 `per`）
- `名称(数字kcal, 数字g蛋白, 数字g碳水, 数字g脂肪)`：括号内数值优先
- 任何一项无法识别时，整条都不会保存

## 文件说明

| 文件 | 作用 |
|---|---|
| `foods.yaml` | **你的食物库**，用 VS Code 打开修改，保存即生效（保持 UTF-8 编码） |
| `config.yaml` | 每日热量 / 蛋白质目标 |
| `data\diet.db` | 所有记录（SQLite）。**备份就复制这个文件** |
| `reports\` | 生成的趋势图 |
| `server.py` | MCP 服务器（Claude 调用的工具） |
| `cli.py` | 命令行版 |
| `diet_agent\` | 解析（parser）、计算与存储（db）、文字报表（report）、趋势图（chart） |
| `tests\` | 用手册示例校验计算 |
| `.mcp.json` | Claude Code 的接入配置（含本机路径，不上传 GitHub） |

## 上传 GitHub

`.gitignore` 已排除 `.venv/`、`data/`、`reports/`、`.mcp.json` 和缓存，饮食记录不会被上传。

```powershell
git add .
git commit -m "简单写一下改了什么"
git push
```

如果仓库要公开，记得把 `foods.yaml` 换成示例版本（它是你的私人食谱）。

## 说明

- 营养数值来自你自己的手册，仅供个人记录参考，不构成医疗或营养建议。
- `汤2 + 西红柿 + 辣酱` 按 30 kcal / 个西红柿计算，与手册"整锅 405"一致。
