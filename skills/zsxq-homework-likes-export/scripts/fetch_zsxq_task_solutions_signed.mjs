import crypto from "node:crypto";
import fs from "node:fs";

const [tasksFile, cookieFile, xaduidFile, outputFile] = process.argv.slice(2);

if (!tasksFile || !cookieFile || !xaduidFile || !outputFile) {
  console.error("Usage: node fetch_zsxq_task_solutions_signed.mjs <tasks.json> <cookies.json> <xaduid.txt> <output.json>");
  process.exit(2);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function readCookieHeader(path) {
  const raw = JSON.parse(fs.readFileSync(path, "utf8"));
  const cookies = raw.data?.cookies || raw.cookies || raw;
  if (!Array.isArray(cookies)) throw new Error("cookies JSON must contain an array or data.cookies");
  return cookies
    .filter((cookie) => String(cookie.domain || "").includes("zsxq.com"))
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");
}

function signedHeaders(url, cookie, xaduid) {
  const requestId = crypto.randomUUID();
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const signature = crypto
    .createHash("md5")
    .update(`${url} ${timestamp} ${requestId}`)
    .digest("hex");

  return {
    Accept: "application/json, text/plain, */*",
    Cookie: cookie,
    Origin: "https://wx.zsxq.com",
    Referer: "https://wx.zsxq.com/",
    "User-Agent": "Mozilla/5.0",
    "X-Aduid": xaduid,
    "X-Request-Id": requestId,
    "X-Signature": signature,
    "X-Timestamp": timestamp,
    "X-Version": "2.92.0",
  };
}

function simplify(item, fallbackTaskId) {
  const solution = item.solution || {};
  const owner = solution.owner || {};
  return {
    topic_id: String(item.topic_uid || item.topic_id || ""),
    create_time: item.create_time || "",
    title: item.title || "",
    likes_count: item.likes_count || 0,
    comments_count: item.comments_count || 0,
    readers_count: item.readers_count || 0,
    rewards_count: item.rewards_count || 0,
    task_id: String(solution.task_uid || solution.task_id || fallbackTaskId),
    owner: {
      user_id: String(owner.user_id || ""),
      name: owner.name || "",
    },
    text: solution.text || "",
    image_count: Array.isArray(solution.images) ? solution.images.length : 0,
  };
}

async function getJson(url, cookie, xaduid) {
  let last = null;
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    const response = await fetch(url, { headers: signedHeaders(url, cookie, xaduid) });
    const json = await response.json();
    if (response.ok && json.succeeded) return json;
    last = { status: response.status, json };
    await sleep(1200 * attempt);
  }
  throw new Error(`request failed ${url} ${JSON.stringify(last).slice(0, 600)}`);
}

async function fetchTask(task, cookie, xaduid) {
  const solutions = [];
  const seen = new Set();
  let endTime = "";

  for (let page = 1; page <= 30; page += 1) {
    let url = `https://api.zsxq.com/v2/topics/${task.id}/solutions?count=20&direction=backward`;
    if (endTime) url += `&end_time=${encodeURIComponent(endTime)}`;

    const json = await getJson(url, cookie, xaduid);
    const list = json.resp_data?.solutions || [];
    let added = 0;

    for (const item of list) {
      const id = String(item.topic_uid || item.topic_id || "");
      if (id && !seen.has(id)) {
        seen.add(id);
        solutions.push(simplify(item, task.id));
        added += 1;
      }
    }

    if (list.length < 20 || added === 0) break;
    endTime = list[list.length - 1].create_time;
    await sleep(500);
  }

  return { task, solutions };
}

const taskConfig = JSON.parse(fs.readFileSync(tasksFile, "utf8"));
const cookie = readCookieHeader(cookieFile);
const xaduid = fs.readFileSync(xaduidFile, "utf8").trim().replace(/^"|"$/g, "") || crypto.randomUUID();
const tasks = taskConfig.tasks || [];

const results = [];
for (const task of tasks) {
  const result = await fetchTask(task, cookie, xaduid);
  results.push(result);
  console.error(`${task.id}\t${result.solutions.length}\t${task.title}`);
  await sleep(700);
}

const payload = {
  fetched_at: new Date().toISOString(),
  group_id: String(taskConfig.group_id || ""),
  output_prefix: taskConfig.output_prefix || "homework",
  task_count: tasks.length,
  solution_count: results.reduce((sum, result) => sum + result.solutions.length, 0),
  results,
};

fs.writeFileSync(outputFile, JSON.stringify(payload, null, 2));
console.log(outputFile);
