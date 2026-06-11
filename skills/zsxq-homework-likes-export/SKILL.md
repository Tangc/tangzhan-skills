---
name: zsxq-homework-likes-export
description: 知识星球作业点赞统计导出。Use when the user wants to export CSV statistics for a 知识星球 task/homework hashtag or course, including all task topics, all student solution submissions under each task, total likes per student, and per-assignment likes. Especially for “作业点赞统计”, “学员提交作业”, “按作业题统计点赞”, or “导出 CSV”.
---

# 知识星球作业点赞导出

## 核心原则

- 优先使用网页端真实接口 `https://api.zsxq.com/v2/topics/{task_id}/solutions`，因为返回的每条 `solution` 带有父作业 `task_uid`。
- 不要用关键词或时间窗口推断作业归属，除非用户明确接受粗略统计。
- 不要要求用户粘贴 Cookie。打开本地可见浏览器，让用户在浏览器里登录；再用 `agent-browser cookies --json` 导出到 `/tmp` 临时文件。
- 临时 Cookie、`XAduid` 只用于本地抓取，完成后立即删除。不要在终端或最终回答里打印凭证。

## 快速流程

1. 准备任务配置 JSON。
   - 可以复制 `references/tasks.example.json`，填入自己的 `group_id`、作业题 `topic_id` 和标题。
   - 如果用户要换星球、换标签或刷新任务列表，先用 `zsxq-cli group +list`、`zsxq-cli group +hashtags`、`zsxq-cli api call get_hashtag_topics` 获取 `task` 列表，再写成同样结构。
2. 打开网页登录态：
   ```bash
   agent-browser --headed --session zsxq-homework open 'https://wx.zsxq.com/'
   ```
   让用户登录并确认能看到目标星球内容。
3. 导出临时登录态：
   ```bash
   agent-browser --session zsxq-homework cookies --json > /tmp/zsxq_homework_cookies.json
   agent-browser --session zsxq-homework eval "localStorage.getItem('XAduid') || ''" > /tmp/zsxq_homework_xaduid.txt
   ```
4. 抓取每个作业题的真实提交列表：
   ```bash
   SKILL_DIR="$HOME/.codex/skills/zsxq-homework-likes-export"
   node "$SKILL_DIR/scripts/fetch_zsxq_task_solutions_signed.mjs" \
     "$SKILL_DIR/references/tasks.example.json" \
     /tmp/zsxq_homework_cookies.json \
     /tmp/zsxq_homework_xaduid.txt \
     outputs/course_homework_task_solutions_raw_signed.json
   ```
5. 生成 CSV：
   ```bash
   SKILL_DIR="$HOME/.codex/skills/zsxq-homework-likes-export"
   python3 "$SKILL_DIR/scripts/build_homework_likes_csv.py" \
     outputs/course_homework_task_solutions_raw_signed.json \
     outputs
   ```
6. 校验并清理：
   ```bash
   python3 - <<'PY'
   import csv
   detail=list(csv.DictReader(open('outputs/course_homework_submission_likes_detail.csv', encoding='utf-8-sig')))
   summary=list(csv.DictReader(open('outputs/course_homework_likes_by_student.csv', encoding='utf-8-sig')))
   print(len(detail), len(summary))
   print(sum(int(r['likes']) for r in detail), sum(int(r['total_likes']) for r in summary))
   PY
   rm -f /tmp/zsxq_homework_cookies.json /tmp/zsxq_homework_xaduid.txt
   ```

## 输出文件

默认生成：

- `<prefix>_likes_by_student.csv`：学员汇总表，含总点赞数、提交数、每个作业题下点赞数。
- `<prefix>_submission_likes_detail.csv`：提交明细表，含作业题、学员、提交主题、点赞数、评论数、浏览数、链接、摘要。

## 任务配置格式

```json
{
  "group_id": "123456789012",
  "output_prefix": "course_homework",
  "tasks": [
    {"id": "11111111111111111", "title": "示例作业 01：第一次作业"}
  ]
}
```

## 常见问题

- `code=1059`：通常是缺少网页端 `X-Signature` 等请求头。必须用本 skill 的签名抓取脚本，不要直接 `fetch`。
- `401 Unauthorized`：网页登录态失效，让用户在可见浏览器里重新登录。
- CSV 准确度不足：确认使用的是 `*_raw_signed.json` 生成的精确 CSV，而不是旧的关键词匹配脚本输出。
