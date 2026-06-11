---
name: zsxq-tuwen-likes-export
description: 知识星球汇总贴图文点赞统计导出。Use when the user provides a 知识星球 article/topic 汇总贴 and wants to extract rows containing “图文” plus 星球内链接, confirm the extracted topic list and rules first, then export per-topic like details and per-author CSV summaries.
---

# 知识星球图文点赞统计导出

## 核心原则

- 必须先让用户提供汇总贴：通常是 `https://articles.zsxq.com/id_xxx.html`，也可以是知识星球主题链接。
- 必须先读取汇总贴并展示图文主题列表，请用户确认后再统计点赞。
- 确认时必须说明统计规则；如果列表不符合用户预期，提醒用户自行修改汇总贴内容格式，然后重新读取预览。
- 不要根据日期、小标题、相邻行或上下文猜测链接归属。格式不规范时不人工补链。
- 确认前只做列表预览；确认后再按确认过的预览 JSON 抓取当前点赞数并导出 CSV。

## 统计规则

默认规则必须原样告诉用户：

1. 逐段/逐行解析汇总贴内容。
2. 仅纳入同一段/同一行里同时包含 `图文` 和知识星球链接的链接。
3. `t.zsxq.com` 短链通过重定向解析 `topic_id`；`wx.zsxq.com` 主题链接直接解析 `topic_id`。
4. 同一行里有多个知识星球主题链接时全部纳入。
5. 微信视频号、公众号、外部网页等非知识星球链接不纳入。
6. 如果 `图文` 和链接被拆到不同行，默认不纳入；请用户先自行修改汇总贴格式，再重新预览。
7. 点赞数来自主题详情接口当前返回的 `counts.likes`，结果会随用户后续点赞变化。

## 快速流程

1. 确认用户提供了汇总贴 URL；若没有，先要求用户提供。
2. 运行预览命令：
   ```bash
   SKILL_DIR="$HOME/.codex/skills/zsxq-tuwen-likes-export"
   python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" preview \
     --source-url '<汇总贴URL>' \
     --out-dir outputs \
     --prefix summary
   ```
3. 打开脚本输出的 `*_preview.md` 或读取终端摘要，把图文主题列表和上面的统计规则发给用户确认。
4. 如果用户指出缺漏或归属错误，不要继续统计；提醒用户先修改汇总贴，让每条图文和对应链接在同一段/同一行，然后重新运行预览。
5. 用户明确确认无误后，运行导出命令：
   ```bash
   SKILL_DIR="$HOME/.codex/skills/zsxq-tuwen-likes-export"
   python3 "$SKILL_DIR/scripts/tuwen_likes_export.py" export \
     --preview-json outputs/summary_tuwen_preview.json \
     --out-dir outputs \
     --prefix summary
   ```
6. 校验 CSV：
   ```bash
   python3 - <<'PY'
   import csv
   detail=list(csv.DictReader(open('outputs/summary_tuwen_like_details.csv', encoding='utf-8-sig')))
   summary=list(csv.DictReader(open('outputs/summary_tuwen_likes_by_author.csv', encoding='utf-8-sig')))
   print(len(detail), len(summary))
   print(sum(int(r['likes_count']) for r in detail), sum(int(r['total_likes']) for r in summary))
   print(all(r['fetch_success'] == 'True' for r in detail))
   PY
   ```

## 输出文件

预览阶段：

- `<prefix>_tuwen_preview.json`：确认用候选主题清单，导出阶段必须使用这份文件。
- `<prefix>_tuwen_preview.md`：给用户确认的 Markdown 列表。

导出阶段：

- `<prefix>_tuwen_like_details.csv`：图文明细，含主题、作者、点赞、评论、阅读、链接和来源行。
- `<prefix>_tuwen_likes_by_author.csv`：按作者汇总，含主题数、总点赞、平均点赞、最高点赞、总评论、总阅读。
- `<prefix>_tuwen_export.json`：导出诊断数据，便于排查字段或接口问题。

## 常见问题

- 预览列表少了某条：通常是 `图文` 和知识星球链接不在同一段/同一行。让用户修改汇总贴格式后重跑预览。
- 预览列表多了某条：通常是某行同时包含 `图文` 和多个知识星球链接。让用户调整汇总贴，把不需要统计的链接移出该行。
- 短链无法解析：重跑预览；若仍失败，要求用户把短链替换为 `wx.zsxq.com` 主题链接后再试。
- 点赞数和页面看到的不一致：以导出时主题详情接口返回的当前值为准，确认是否刚发生新增点赞或缓存延迟。
