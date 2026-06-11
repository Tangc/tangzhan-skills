#!/usr/bin/env python3
import argparse
import csv
import json
import re
import subprocess
import time
import urllib.parse
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_paragraph = False
        self.text = []
        self.links = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_paragraph = True
            self.text = []
            self.links = []
        if self.in_paragraph and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        if self.in_paragraph and tag == "br":
            self.text.append("\n")

    def handle_data(self, data):
        if self.in_paragraph:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.in_paragraph:
            self.rows.append((clean_text("".join(self.text)), list(self.links)))
            self.in_paragraph = False


def clean_text(value):
    return " ".join((value or "").split())


def run_json(command, timeout=60):
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command did not return JSON: {' '.join(command)}\n{result.stdout}\n{result.stderr}") from exc


def article_id_from_url(source_url):
    match = re.search(r"/id_([A-Za-z0-9]+)\.html", source_url)
    if match:
        return match.group(1)
    parsed = urllib.parse.urlparse(source_url)
    match = re.search(r"id_([A-Za-z0-9]+)", parsed.path)
    return match.group(1) if match else ""


def topic_id_from_url(source_url):
    parsed = urllib.parse.urlparse(source_url)
    query_topic_id = urllib.parse.parse_qs(parsed.query).get("topic_id", [""])[0]
    if query_topic_id:
        return query_topic_id
    for pattern in (r"/topic/(\d+)", r"/homework/(\d+)"):
        match = re.search(pattern, source_url)
        if match:
            return match.group(1)
    return ""


def fetch_source(source_url):
    article_id = article_id_from_url(source_url)
    if article_id:
        data = run_json(["zsxq-cli", "api", "raw", "--method", "GET", "--path", f"/v2/articles/{article_id}"])
        return {
            "source_type": "article",
            "source_url": source_url,
            "title": data.get("title", ""),
            "content": data.get("content") or data.get("original_content") or "",
            "topic_id": str(data.get("topic_id") or ""),
        }

    topic_id = topic_id_from_url(source_url)
    if topic_id:
        data = run_json([
            "zsxq-cli", "api", "call", "get_topic_info",
            "--params", json.dumps({"topic_id": topic_id}, ensure_ascii=False),
        ])
        topic = data.get("topic") or {}
        return {
            "source_type": "topic",
            "source_url": source_url,
            "title": topic.get("title", ""),
            "content": topic.get("content") or "",
            "topic_id": topic_id,
        }

    raise RuntimeError("cannot parse article id or topic id from source URL")


def split_rows(content):
    if "<p" in content and "</p>" in content:
        parser = ParagraphParser()
        parser.feed(content)
        return parser.rows

    rows = []
    url_pattern = re.compile(r"https?://\S+")
    for line in content.splitlines():
        text = clean_text(line)
        if not text:
            continue
        rows.append((text, url_pattern.findall(text)))
    return rows


def resolve_topic_link(url):
    if "t.zsxq.com" in url:
        for attempt in range(3):
            result = subprocess.run(
                ["curl", "-s", "-L", "-o", "/dev/null", "-w", "%{url_effective}", url],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            effective_url = result.stdout.strip()
            topic_id = topic_id_from_url(effective_url)
            if topic_id:
                return topic_id, effective_url
            time.sleep(0.4 * (attempt + 1))
        return "", ""

    return topic_id_from_url(url), url


def fetch_topic(topic_id):
    last_data = {}
    for attempt in range(3):
        last_data = run_json([
            "zsxq-cli", "api", "call", "get_topic_info",
            "--params", json.dumps({"topic_id": topic_id}, ensure_ascii=False),
        ], timeout=70)
        if last_data.get("success"):
            return last_data
        time.sleep(0.8 * (attempt + 1))
    return last_data


def first_title(topic):
    if topic.get("title"):
        return clean_text(topic["title"])
    for line in (topic.get("content") or "").splitlines():
        line = clean_text(line)
        if line:
            return line
    return ""


def count_value(counts, names):
    for name in names:
        value = counts.get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def make_topic_url(group_id, topic_id):
    if group_id and topic_id:
        return f"https://wx.zsxq.com/group/{group_id}/topic/{topic_id}"
    return ""


def preview(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source = fetch_source(args.source_url)
    extracted = []
    for row_no, (text, links) in enumerate(split_rows(source["content"]), 1):
        zsxq_links = [link for link in links if "zsxq.com" in link]
        if "图文" not in text or not zsxq_links:
            continue
        for source_link in zsxq_links:
            topic_id, effective_url = resolve_topic_link(source_link)
            extracted.append({
                "row_no": row_no,
                "source_line": text,
                "source_link": source_link,
                "effective_url": effective_url,
                "topic_id": topic_id,
            })

    seen = []
    for item in extracted:
        if item["topic_id"] and item["topic_id"] not in seen:
            seen.append(item["topic_id"])

    topics = {}
    for topic_id in seen:
        data = fetch_topic(topic_id)
        topic = data.get("topic") or {}
        owner = topic.get("owner") or {}
        group = topic.get("group") or {}
        topics[topic_id] = {
            "fetch_success": bool(data.get("success")),
            "topic_id": topic_id,
            "topic_title": first_title(topic),
            "topic_type": topic.get("type") or "",
            "create_time": topic.get("create_time") or "",
            "author_id": owner.get("user_id") or owner.get("id") or "",
            "author_name": owner.get("name") or "",
            "group_id": str(group.get("group_id") or args.group_id or ""),
        }

    rows = []
    for index, item in enumerate([item for item in extracted if item["topic_id"]], 1):
        topic = topics.get(item["topic_id"], {})
        rows.append({
            "seq": index,
            **item,
            **topic,
            "topic_url": make_topic_url(topic.get("group_id", ""), item["topic_id"]),
        })

    preview_json = out_dir / f"{args.prefix}_tuwen_preview.json"
    preview_md = out_dir / f"{args.prefix}_tuwen_preview.md"
    payload = {
        "source": source,
        "rules": [
            "仅纳入同一段/同一行里同时包含“图文”和知识星球链接的链接。",
            "短链解析为 topic_id；同一行多个知识星球主题链接全部纳入。",
            "不根据日期、小标题、相邻行或上下文猜测链接归属。",
            "确认后按主题详情接口当前 counts.likes 导出点赞数。",
        ],
        "unresolved_items": [item for item in extracted if not item["topic_id"]],
        "rows": rows,
    }
    preview_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# 图文统计预览：{source.get('title') or args.source_url}",
        "",
        f"- 候选主题数：{len(rows)}",
        f"- 未解析链接数：{len(payload['unresolved_items'])}",
        "",
        "## 统计规则",
        "",
    ]
    lines.extend(f"- {rule}" for rule in payload["rules"])
    lines.extend(["", "## 图文列表", ""])
    for row in rows:
        lines.append(f"{row['seq']}. [{row['topic_title']}]({row['topic_url']}) - {row['author_name']} - 来源行：{row['source_line']}")
    if payload["unresolved_items"]:
        lines.extend(["", "## 未解析链接", ""])
        for item in payload["unresolved_items"]:
            lines.append(f"- 第 {item['row_no']} 行：{item['source_link']}；来源行：{item['source_line']}")
    preview_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "preview_json": str(preview_json),
        "preview_md": str(preview_md),
        "topic_count": len(rows),
        "unresolved_count": len(payload["unresolved_items"]),
    }, ensure_ascii=False, indent=2))
    return 0


def export(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_data = json.loads(Path(args.preview_json).read_text(encoding="utf-8"))
    rows = preview_data.get("rows", [])
    topics = {}
    for row in rows:
        topic_id = row["topic_id"]
        if topic_id in topics:
            continue
        data = fetch_topic(topic_id)
        topic = data.get("topic") or {}
        counts = topic.get("counts") or {}
        owner = topic.get("owner") or {}
        group = topic.get("group") or {}
        topics[topic_id] = {
            "fetch_success": bool(data.get("success")),
            "topic_id": topic_id,
            "topic_title": first_title(topic) or row.get("topic_title", ""),
            "topic_type": topic.get("type") or row.get("topic_type", ""),
            "create_time": topic.get("create_time") or row.get("create_time", ""),
            "author_id": owner.get("user_id") or owner.get("id") or row.get("author_id", ""),
            "author_name": owner.get("name") or row.get("author_name", ""),
            "group_id": str(group.get("group_id") or row.get("group_id") or ""),
            "likes_count": count_value(counts, ["likes", "likes_count", "like_count", "liked_count"]),
            "comments_count": count_value(counts, ["comments", "comments_count", "comment_count"]),
            "readers_count": count_value(counts, ["readers", "readers_count", "reading_count", "read_count"]),
            "raw_counts": counts,
        }
        time.sleep(0.1)

    detail_rows = []
    for index, row in enumerate(rows, 1):
        topic = topics[row["topic_id"]]
        detail_rows.append({
            "seq": index,
            "row_no": row["row_no"],
            "source_line": row["source_line"],
            "topic_id": row["topic_id"],
            "topic_title": topic["topic_title"],
            "author_id": topic["author_id"],
            "author_name": topic["author_name"],
            "likes_count": topic["likes_count"],
            "comments_count": topic["comments_count"],
            "readers_count": topic["readers_count"],
            "create_time": topic["create_time"],
            "topic_url": make_topic_url(topic["group_id"], row["topic_id"]),
            "source_link": row["source_link"],
            "effective_url": row["effective_url"],
            "fetch_success": topic["fetch_success"],
        })

    detail_csv = out_dir / f"{args.prefix}_tuwen_like_details.csv"
    author_csv = out_dir / f"{args.prefix}_tuwen_likes_by_author.csv"
    export_json = out_dir / f"{args.prefix}_tuwen_export.json"

    with detail_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()) if detail_rows else [])
        writer.writeheader()
        writer.writerows(detail_rows)

    summary = defaultdict(lambda: {
        "author_id": "",
        "author_name": "",
        "topic_count": 0,
        "total_likes": 0,
        "avg_likes": 0,
        "max_likes": 0,
        "total_comments": 0,
        "total_readers": 0,
    })
    for row in detail_rows:
        key = row["author_id"] or row["author_name"] or "unknown"
        item = summary[key]
        item["author_id"] = row["author_id"]
        item["author_name"] = row["author_name"] or "unknown"
        item["topic_count"] += 1
        item["total_likes"] += int(row["likes_count"] or 0)
        item["max_likes"] = max(item["max_likes"], int(row["likes_count"] or 0))
        item["total_comments"] += int(row["comments_count"] or 0)
        item["total_readers"] += int(row["readers_count"] or 0)

    summary_rows = []
    for item in summary.values():
        item["avg_likes"] = round(item["total_likes"] / item["topic_count"], 2) if item["topic_count"] else 0
        summary_rows.append(dict(item))
    summary_rows.sort(key=lambda item: (-item["total_likes"], -item["topic_count"], item["author_name"]))

    with author_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["author_id", "author_name", "topic_count", "total_likes", "avg_likes", "max_likes", "total_comments", "total_readers"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    export_json.write_text(json.dumps({
        "source": preview_data.get("source", {}),
        "rules": preview_data.get("rules", []),
        "rows": detail_rows,
        "summary": summary_rows,
        "topics": topics,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "detail_csv": str(detail_csv),
        "author_csv": str(author_csv),
        "export_json": str(export_json),
        "topic_count": len(detail_rows),
        "author_count": len(summary_rows),
        "total_likes": sum(int(row["likes_count"] or 0) for row in detail_rows),
        "all_fetch_success": all(row["fetch_success"] for row in detail_rows),
    }, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Export ZSXQ tuwen topic likes from a confirmed summary post preview.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("--source-url", required=True)
    preview_parser.add_argument("--group-id", default="")
    preview_parser.add_argument("--out-dir", default="outputs")
    preview_parser.add_argument("--prefix", default="summary")
    preview_parser.set_defaults(func=preview)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--preview-json", required=True)
    export_parser.add_argument("--out-dir", default="outputs")
    export_parser.add_argument("--prefix", default="summary")
    export_parser.set_defaults(func=export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
