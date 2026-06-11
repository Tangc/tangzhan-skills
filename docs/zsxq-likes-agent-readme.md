# 给 Agent 的知识星球点赞统计任务说明

这份文档是给 Agent 读的。用户只需要把本文件交给 Agent，并说明自己要做“作业点赞统计”或“图文点赞统计”，Agent 应按下面流程完成安装、确认、导出和交付。

## 你可以完成什么

你可以用本仓库的两个 skill 完成两类任务：

- `zsxq-homework-likes-export`：统计知识星球作业题下所有学员提交的点赞数，输出学员汇总 CSV 和提交明细 CSV。
- `zsxq-tuwen-likes-export`：从知识星球汇总贴中提取“图文 + 知识星球链接”，确认列表后输出图文点赞明细 CSV 和按作者汇总 CSV。

不要把这两个任务混在一起。先判断用户要的是哪一种统计，再进入对应流程。

## 安装

如果本机还没有安装 skill，先执行：

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-homework-likes-export
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-tuwen-likes-export
```

安装后提醒用户重启 Agent 客户端，确保 skill 被重新加载。若当前会话无法重启，可以继续用已安装目录里的脚本执行，但要在最终结果中说明这一点。

## 开始前检查

开始执行前，先确认：

- `python3` 可用。
- `node` 可用。
- `curl` 可用。
- `zsxq-cli` 已安装且已登录。
- 作业点赞统计还需要 `agent-browser` 可用。

可以使用下面命令做只读检查：

```bash
python3 --version
node --version
curl --version
zsxq-cli auth status
agent-browser --version
```

如果某项缺失，先向用户说明缺什么，不要伪造统计结果。

## 安全规则

必须遵守：

- 不要要求用户在聊天里粘贴 Cookie、`XAduid` 或其他登录凭证。
- Cookie 和 `XAduid` 只能保存到 `/tmp` 临时文件。
- 不要把 Cookie、`XAduid`、raw JSON、CSV 输出或用户的私有配置提交到 Git。
- 完成作业点赞统计后，删除 `/tmp/zsxq_homework_cookies.json` 和 `/tmp/zsxq_homework_xaduid.txt`。
- 只统计用户有权限访问的知识星球内容。
- 点赞数以导出当时接口返回值为准。

## 用户需要提供什么

如果用户要做作业点赞统计，让用户提供：

- 目标星球 ID，也就是 `group_id`。
- 作业题主题 ID 列表，也就是每个作业题的 `topic_id`。
- 每个作业题的标题。
- 输出文件名前缀，例如 `course_homework`。

如果用户还没有整理任务列表，你可以协助用户用 `zsxq-cli` 查询星球、标签和主题，再生成 `tasks.json`。

如果用户要做图文点赞统计，让用户提供：

- 汇总贴 URL，通常形如 `https://articles.zsxq.com/id_xxx.html`。
- 或知识星球主题 URL。

图文统计必须先预览候选列表，并让用户确认后再导出。

## 作业点赞统计流程

适用于：统计课程、训练营、打卡活动中，多个作业题下所有学员提交的点赞数。

### 1. 创建任务配置

复制示例配置：

```bash
cp "$HOME/.codex/skills/zsxq-homework-likes-export/references/tasks.example.json" ./tasks.json
```

把 `tasks.json` 改成用户自己的数据：

```json
{
  "group_id": "123456789012",
  "output_prefix": "course_homework",
  "tasks": [
    {
      "id": "11111111111111111",
      "title": "示例作业 01：第一次作业"
    }
  ]
}
```

不要使用示例 ID 直接统计。

### 2. 打开浏览器让用户登录

```bash
agent-browser --headed --session zsxq-homework open 'https://wx.zsxq.com/'
```

让用户在可见浏览器里登录，并确认可以看到目标星球内容。

### 3. 导出临时登录态

```bash
agent-browser --session zsxq-homework cookies --json > /tmp/zsxq_homework_cookies.json
agent-browser --session zsxq-homework eval "localStorage.getItem('XAduid') || ''" > /tmp/zsxq_homework_xaduid.txt
```

不要打印这两个文件的内容。

### 4. 抓取作业提交

```bash
SKILL_DIR="$HOME/.codex/skills/zsxq-homework-likes-export"
mkdir -p outputs

node "$SKILL_DIR/scripts/fetch_zsxq_task_solutions_signed.mjs" \
  ./tasks.json \
  /tmp/zsxq_homework_cookies.json \
  /tmp/zsxq_homework_xaduid.txt \
  outputs/course_homework_task_solutions_raw_signed.json
```

如果用户使用了不同的 `output_prefix`，输出 raw JSON 文件名也应对应调整。

### 5. 生成 CSV

```bash
python3 "$SKILL_DIR/scripts/build_homework_likes_csv.py" \
  outputs/course_homework_task_solutions_raw_signed.json \
  outputs
```

输出文件：

- `outputs/<prefix>_likes_by_student.csv`
- `outputs/<prefix>_submission_likes_detail.csv`

### 6. 校验并清理

```bash
python3 - <<'PY'
import csv
from pathlib import Path

summary = next(Path("outputs").glob("*_likes_by_student.csv"))
detail = next(Path("outputs").glob("*_submission_likes_detail.csv"))

detail_rows = list(csv.DictReader(detail.open(encoding="utf-8-sig")))
summary_rows = list(csv.DictReader(summary.open(encoding="utf-8-sig")))

print("detail_rows", len(detail_rows))
print("summary_rows", len(summary_rows))
print("detail_total_likes", sum(int(r["likes"] or 0) for r in detail_rows))
print("summary_total_likes", sum(int(r["total_likes"] or 0) for r in summary_rows))
PY

rm -f /tmp/zsxq_homework_cookies.json /tmp/zsxq_homework_xaduid.txt
```

最终回复用户时，说明：

- 统计了多少个作业题。
- 统计了多少条提交。
- 覆盖多少名学员。
- 总点赞数是多少。
- 两个 CSV 文件路径。

## 图文点赞统计流程

适用于：用户有一篇汇总贴，里面列出多条图文和对应知识星球链接，需要按图文和作者统计点赞。

### 1. 预览候选图文列表

```bash
SKILL_DIR="$HOME/.codex/skills/zsxq-tuwen-likes-export"
mkdir -p outputs

python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" preview \
  --source-url '<汇总贴URL>' \
  --out-dir outputs \
  --prefix summary
```

输出：

- `outputs/summary_tuwen_preview.json`
- `outputs/summary_tuwen_preview.md`

### 2. 必须让用户确认

把预览结果和统计规则发给用户确认。确认前不要执行 export。

必须说明这些规则：

- 仅纳入同一段或同一行里同时包含 `图文` 和知识星球链接的链接。
- `t.zsxq.com` 短链会通过重定向解析 `topic_id`。
- `wx.zsxq.com` 主题链接会直接解析 `topic_id`。
- 同一行里有多个知识星球主题链接时全部纳入。
- 微信视频号、公众号、外部网页等非知识星球链接不纳入。
- 如果 `图文` 和链接被拆到不同行，默认不纳入。
- 点赞数来自导出时主题详情接口当前返回值。

如果用户说列表不对，停止导出，让用户修改汇总贴格式后重新预览。

### 3. 用户确认后导出

```bash
python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" export \
  --preview-json outputs/summary_tuwen_preview.json \
  --out-dir outputs \
  --prefix summary
```

输出文件：

- `outputs/summary_tuwen_like_details.csv`
- `outputs/summary_tuwen_likes_by_author.csv`
- `outputs/summary_tuwen_export.json`

### 4. 校验

```bash
python3 - <<'PY'
import csv

detail = list(csv.DictReader(open("outputs/summary_tuwen_like_details.csv", encoding="utf-8-sig")))
summary = list(csv.DictReader(open("outputs/summary_tuwen_likes_by_author.csv", encoding="utf-8-sig")))

print("topic_count", len(detail))
print("author_count", len(summary))
print("total_likes", sum(int(r["likes_count"] or 0) for r in detail))
print("all_fetch_success", all(r["fetch_success"] == "True" for r in detail))
PY
```

最终回复用户时，说明：

- 统计了多少篇图文。
- 覆盖多少位作者。
- 总点赞数是多少。
- 是否所有主题抓取成功。
- CSV 文件路径。

## 常见失败处理

### `401 Unauthorized`

登录态失效。让用户重新登录知识星球，再重新导出临时登录态。

### `code=1059`

通常是缺少网页端签名请求头。作业点赞统计必须使用 `fetch_zsxq_task_solutions_signed.mjs`。

### `zsxq-cli` 无法读取文章或主题

先检查 `zsxq-cli auth status`。如果未登录，让用户登录后重试。

### 图文预览列表缺漏

通常是汇总贴格式不符合规则。让用户把 `图文` 和对应知识星球链接放在同一段或同一行，然后重新预览。

## 最终交付格式

最终回答要简洁，优先给结果和文件路径。例如：

```text
已完成知识星球图文点赞统计。

- 图文数：32
- 作者数：18
- 总点赞：426
- 抓取状态：全部成功
- 明细 CSV：outputs/summary_tuwen_like_details.csv
- 作者汇总 CSV：outputs/summary_tuwen_likes_by_author.csv
```

不要在最终回答里粘贴 Cookie、raw JSON 或大段 CSV 内容。
