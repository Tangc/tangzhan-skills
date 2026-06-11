#!/usr/bin/env python3
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def clean_text(value: str) -> str:
    return " ".join((value or "").split())


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 build_homework_likes_csv.py <raw_solutions.json> <output_dir>", file=sys.stderr)
        return 2

    raw_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(raw_path.read_text(encoding="utf-8"))
    group_id = str(data.get("group_id") or "")
    prefix = data.get("output_prefix") or raw_path.stem.replace("_task_solutions_raw_signed", "")
    if not prefix:
        prefix = "homework"

    summary_csv = output_dir / f"{prefix}_likes_by_student.csv"
    detail_csv = output_dir / f"{prefix}_submission_likes_detail.csv"

    tasks = [item["task"] for item in data["results"]]
    task_titles = {task["id"]: task["title"] for task in tasks}

    detail_rows = []
    for result in data["results"]:
        task = result["task"]
        for solution in result["solutions"]:
            owner = solution.get("owner", {})
            topic_id = solution.get("topic_id", "")
            detail_rows.append({
                "assignment_topic_id": task["id"],
                "assignment_title": task["title"],
                "student_user_id": owner.get("user_id", ""),
                "student_name": owner.get("name", ""),
                "submission_topic_id": topic_id,
                "submission_time": solution.get("create_time", ""),
                "likes": solution.get("likes_count", 0),
                "comments": solution.get("comments_count", 0),
                "readers": solution.get("readers_count", 0),
                "image_count": solution.get("image_count", 0),
                "submission_url": f"https://wx.zsxq.com/group/{group_id}/topic/{topic_id}" if group_id and topic_id else "",
                "content_excerpt": clean_text(solution.get("text", ""))[:180],
            })

    detail_rows.sort(key=lambda row: (
        row["assignment_topic_id"],
        row["submission_time"],
        row["submission_topic_id"],
    ))

    per_student = defaultdict(lambda: {"name": "", "total": 0, "count": 0, "assignments": defaultdict(int)})
    for row in detail_rows:
        sid = row["student_user_id"] or row["student_name"]
        likes = int(row["likes"] or 0)
        per_student[sid]["name"] = row["student_name"]
        per_student[sid]["total"] += likes
        per_student[sid]["count"] += 1
        per_student[sid]["assignments"][row["assignment_topic_id"]] += likes

    with detail_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "assignment_topic_id", "assignment_title", "student_user_id", "student_name",
            "submission_topic_id", "submission_time", "likes", "comments", "readers",
            "image_count", "submission_url", "content_excerpt",
        ])
        writer.writeheader()
        writer.writerows(detail_rows)

    fields = ["student_user_id", "student_name", "total_likes", "submission_count"]
    fields.extend(task_titles[task["id"]] for task in tasks)
    with summary_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for sid, row_data in sorted(per_student.items(), key=lambda item: (-item[1]["total"], item[1]["name"])):
            row = {
                "student_user_id": sid,
                "student_name": row_data["name"],
                "total_likes": row_data["total"],
                "submission_count": row_data["count"],
            }
            for task in tasks:
                row[task_titles[task["id"]]] = row_data["assignments"].get(task["id"], 0)
            writer.writerow(row)

    print(f"tasks={len(tasks)}")
    print(f"submissions={len(detail_rows)}")
    print(f"students={len(per_student)}")
    print(f"total_likes={sum(int(row['likes'] or 0) for row in detail_rows)}")
    print(summary_csv)
    print(detail_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
