# 知识星球点赞统计 Skills 使用说明

本仓库提供两个知识星球点赞统计 skill：

- `zsxq-homework-likes-export`：统计作业题下所有学员提交的点赞数，导出学员汇总和提交明细 CSV。
- `zsxq-tuwen-likes-export`：从汇总贴中提取“图文 + 知识星球链接”，确认列表后导出图文点赞明细和按作者汇总 CSV。

如果你想让 Agent 直接替你完成统计，把 [给 Agent 的任务说明](zsxq-likes-agent-readme.md) 发给 Agent，并同时提供你的作业题列表或汇总贴 URL。

## 安装

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-homework-likes-export
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-tuwen-likes-export
```

安装后重启你的 Agent 客户端，让新的 skill 被重新加载。

## 依赖

通用依赖：

- `python3`
- `node`
- `curl`
- 已登录并可调用的 `zsxq-cli`

作业点赞统计还需要：

- `agent-browser`
- 一个可见浏览器登录态，用于本地临时导出知识星球网页端 Cookie

## 安全边界

- 不要把 Cookie、`XAduid`、临时登录文件、原始接口 JSON 或真实 CSV 提交到仓库。
- 不要在聊天记录、终端输出或 issue 中粘贴 Cookie。
- 只统计你有权限访问的星球内容。
- 点赞数来自导出时接口返回的当前值，后续新增点赞会改变结果。

## 作业点赞统计

适用场景：课程、训练营或社群里，每个作业题都有学员在题目下提交作业，需要统计每个学员的总点赞和每次作业点赞。

### 1. 准备任务配置

复制示例文件并填入自己的星球和作业题信息：

```bash
cp "$HOME/.codex/skills/zsxq-homework-likes-export/references/tasks.example.json" ./tasks.json
```

配置格式：

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

字段说明：

- `group_id`：知识星球的星球 ID。
- `output_prefix`：输出文件名前缀。
- `tasks[].id`：作业题主题 ID。
- `tasks[].title`：作业题标题，会作为 CSV 列名或明细字段。

### 2. 登录并导出临时登录态

```bash
agent-browser --headed --session zsxq-homework open 'https://wx.zsxq.com/'
```

在浏览器里登录并确认能看到目标星球内容，然后导出临时登录态：

```bash
agent-browser --session zsxq-homework cookies --json > /tmp/zsxq_homework_cookies.json
agent-browser --session zsxq-homework eval "localStorage.getItem('XAduid') || ''" > /tmp/zsxq_homework_xaduid.txt
```

### 3. 抓取作业提交

```bash
SKILL_DIR="$HOME/.codex/skills/zsxq-homework-likes-export"
mkdir -p outputs

node "$SKILL_DIR/scripts/fetch_zsxq_task_solutions_signed.mjs" \
  ./tasks.json \
  /tmp/zsxq_homework_cookies.json \
  /tmp/zsxq_homework_xaduid.txt \
  outputs/course_homework_task_solutions_raw_signed.json
```

### 4. 生成 CSV

```bash
python3 "$SKILL_DIR/scripts/build_homework_likes_csv.py" \
  outputs/course_homework_task_solutions_raw_signed.json \
  outputs
```

默认输出：

- `outputs/course_homework_likes_by_student.csv`
- `outputs/course_homework_submission_likes_detail.csv`

完成后清理临时登录文件：

```bash
rm -f /tmp/zsxq_homework_cookies.json /tmp/zsxq_homework_xaduid.txt
```

## 图文点赞统计

适用场景：你有一篇知识星球汇总贴，里面按行或段落列出了“图文”和对应知识星球链接，需要统计每篇图文的点赞并按作者汇总。

### 1. 预览图文列表

```bash
SKILL_DIR="$HOME/.codex/skills/zsxq-tuwen-likes-export"
mkdir -p outputs

python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" preview \
  --source-url '<汇总贴URL>' \
  --out-dir outputs \
  --prefix summary
```

预览阶段会生成：

- `outputs/summary_tuwen_preview.json`
- `outputs/summary_tuwen_preview.md`

先检查预览列表，确认纳入统计的主题正确，再进入导出阶段。

### 2. 导出点赞 CSV

```bash
python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" export \
  --preview-json outputs/summary_tuwen_preview.json \
  --out-dir outputs \
  --prefix summary
```

默认输出：

- `outputs/summary_tuwen_like_details.csv`
- `outputs/summary_tuwen_likes_by_author.csv`
- `outputs/summary_tuwen_export.json`

## 图文提取规则

- 仅纳入同一段或同一行里同时包含 `图文` 和知识星球链接的链接。
- `t.zsxq.com` 短链会通过重定向解析 `topic_id`。
- `wx.zsxq.com` 主题链接会直接解析 `topic_id`。
- 同一行里有多个知识星球主题链接时全部纳入。
- 微信视频号、公众号、外部网页等非知识星球链接不纳入。
- 如果 `图文` 和链接被拆到不同行，默认不纳入；请先修改汇总贴格式后重新预览。

## 常见问题

### `401 Unauthorized`

登录态失效。重新打开可见浏览器登录知识星球，再导出临时 Cookie。

### `code=1059`

通常是缺少网页端签名请求头。作业统计请使用 `fetch_zsxq_task_solutions_signed.mjs`，不要直接请求接口。

### 图文列表少了某条

通常是 `图文` 和知识星球链接不在同一段或同一行。修改汇总贴格式后重新运行预览。

### 点赞数和页面不一致

以导出时接口返回的当前值为准。若有人刚刚点赞，页面缓存和接口返回可能短时间不一致。
