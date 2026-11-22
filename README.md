# 减脂饮食管家（自用版）

在 Claude Desktop 里像平时一样说话："早标A + 饼包"、"汤2 + 8只虾 - 橄榄油"。
Claude 负责听懂，**计算和存档全部由本地代码完成**——不会算错，数据跨对话保留在你电脑上。

## 一次性安装（Windows）

### 1. 安装 Python
到 python.org 下载 Python 3.12 或更新版本的 Windows 安装包。安装时**务必勾选底部的「Add python.exe to PATH」**。
装好后打开「命令提示符」（开始菜单搜 cmd），输入 `py --version`，能看到版本号就行。

### 2. 解压并安装依赖
把 diet-agent.zip 解压到 `文档` 文件夹，然后在命令提示符里依次输入：

```bat
cd %USERPROFILE%\Documents\diet-agent
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. 自测
```bat
.venv\Scripts\python -m pytest -q tests
.venv\Scripts\python cli.py calc "早标A + 饼4 + 汤1 + 果-C"
```
第一行应显示 `16 passed`，第二行应算出 970 kcal。

### 4. 记下完整路径
```bat
cd
```
会显示类似 `C:\Users\Alice\Documents\diet-agent`，下一步要用。

## 接入 Claude Desktop

1. 打开 Claude Desktop → 左上角菜单 → 设置（Settings）→ 开发者（Developer）→ 编辑配置（Edit Config）。它会打开 `claude_desktop_config.json`（用记事本打开即可）。
2. 填入下面内容，把 `Alice` 换成你的用户名。**路径里的反斜杠要写两个 `\\`**：

```json
{
  "mcpServers": {
    "diet": {
      "command": "C:\\Users\\Alice\\Documents\\diet-agent\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Alice\\Documents\\diet-agent\\server.py"]
    }
  }
}
```

如果文件里已经有其他内容，只把 `"diet": {...}` 这一段加进 `mcpServers` 里，注意逗号。

3. 保存后，**在任务栏右下角托盘里右键 Claude 图标 → 退出**（只关窗口不算退出），再重新打开。
4. 在对话框的工具/连接器列表里看到「减脂饮食管家」就成功了。

### 常见问题
- **连接失败**：设置 → 开发者里会显示错误。九成是路径写错或反斜杠只写了一个。
- **`py` 不是内部命令**：安装 Python 时没勾选 PATH，重新运行安装包选「Modify」勾上即可。
- **用 Notepad 保存后 JSON 报错**：检查引号是否变成了中文引号。

## 日常使用

直接对 Claude 说：

| 你说 | 发生什么 |
|---|---|
| `早餐：早标A + 饼包` | 记录并告诉你今天还剩多少 |
| `午餐 汤1*0.5 + 肉-鸡胸` | 喝了半锅汤 |
| `汤2 + 8只虾 - 橄榄油 + 2勺辣酱` | 临时加减 |
| `外食健康餐(730kcal, 48g蛋白)` | 直接采用你报的数 |
| `吃了一块披萨` | 库里没有 → Claude 估算后记录，标【估算】 |
| `收官` | 今日明细 + 存档行 |
| `这周怎么样` | 最近 7 天每日数据和日均 |
| `删掉 #5` | 删除记错的条目 |
| `把 XX 加进食物库，每份 … kcal` | 新增代号 |

## 速记语法

- `+` 连接，`-` 减去（代号里自带的 `-` 如 `果-C` 会自动识别）；`、` `，` 也当作 `+`
- `饼4` = 4块；`汤1*0.5` 或 `汤1×0.5` = 半份；`半碗碗1` = 半份
- `8只虾`：按"一份 = 8只"折算（foods.yaml 里的 `per`）
- `名称(数字kcal, 数字g蛋白, 数字g碳水, 数字g脂肪)`：括号内数值优先

## 文件说明

| 文件 | 作用 |
|---|---|
| `foods.yaml` | **你的食物库**，用记事本或 VS Code 打开修改，保存即生效（保持 UTF-8 编码） |
| `config.yaml` | 每日热量 / 蛋白质目标 |
| `data\diet.db` | 所有记录（SQLite）。备份就复制这个文件 |
| `server.py` | MCP 服务器（Claude 调用的工具） |
| `cli.py` | 命令行版：`calc` / `log` / `today` / `week` / `del` / `foods` |
| `diet_agent/` | 解析、计算、存储、报表 |
| `tests/` | 用手册示例校验计算 |

## 说明

- 营养数值来自你自己的手册，仅供个人记录参考，不构成医疗或营养建议。
- `汤2 + 西红柿 + 辣酱` 按 30 kcal/个西红柿计算，与手册"整锅 405"一致。