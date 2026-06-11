# Tangzhan Skills Collection

这里汇集了一系列高质量的 OpenCode/Sisyphus 技能，旨在提升开发效率、优化内容创作以及增强数据分析能力。

## 📦 技能列表 (Skills)

### 1. 3分力润色大师 (Tangzhan Runse Master)
**核心功能**：技术内容润色引擎。
*   **角色**：作为 "Gemini" 协助 "唐斩" 进行技术内容创作。
*   **特点**：遵循 "3分力" 原则（只改节奏、排版、错别字，保留核心语感），严格执行术语修正（如 Cloud Code -> Claude Code），输出符合 AI Native 风格的 Markdown。
*   **适用场景**：技术博客、公众号文章、朋友圈文案优化。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill tangzhan-runse-master
```

### 2. 代码简化专家 (Code Simplifier)
**核心功能**：代码重构与简化。
*   **目标**：提升代码清晰度、一致性和可维护性，同时**绝对保留原有功能**。
*   **特点**：消除冗余、优化逻辑结构、应用最佳实践（如明确的返回类型、避免嵌套三元运算符），拒绝过度工程化。
*   **适用场景**：代码审查（Code Review）、遗留代码重构、日常开发中的即时优化。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill tangzhan-code-simplifier
```

### 3. 文本转网页设计顾问 (Webpage Designer)
**核心功能**：一键将文本转换为设计感十足的网页。
*   **能力**：内置 **30+ 种精选设计风格**（如 Cyberpunk, SaaS, Minimalist, Neo Brutalism 等）。
*   **智能推荐**：根据文本内容（语气、受众）自动推荐最匹配的设计风格，或接受指定风格。
*   **输出**：单文件、响应式的 HTML 网页。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill tangzhan-webpage-designer
```

### 4. OpenCode 洞察分析师 (OpenCode Insights)
**核心功能**：开发会话深度分析与可视化。
*   **能力**：分析 OpenCode 会话历史，提取工作模式、工具使用频率、摩擦点（Friction Points）和高光时刻（Wins）。
*   **输出**：生成包含图表和策略建议的 `insight-report.html` 报告，帮助开发者复盘和优化工作流。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill tangzhan-skill-opencodeInsights
```

### 5. Agent 每日复盘器 (Agent Retro)
**核心功能**：按日期复盘 Agent 执行质量并固化改进。
*   **能力**：读取指定日期会话与工具动作，按 6 维度输出复盘（动作、做对、做错、改进点、用户画像、Agent 画像）。
*   **输出**：更新 `memory/YYYY-MM-DD.md`，并同步优化 `MEMORY.md`、`USER.md`、`SOUL.md`、`AGENTS.md`，附防重锁文件。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill agent-retro
```

### 6. 即梦 AI 出图助手 (Jimeng)
**核心功能**：调用 Jimeng AI 4.0（火山引擎）进行文生图/图生图，并可选发送至飞书。
*   **能力**：支持纯文本生成或图片参考生成；可配置宽高比、返回数量、反向提示词等参数。
*   **输出**：本地图片文件（含时间戳命名）+ 可选飞书发送。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill jimeng
```

### 7. 飞书语音播报助手 (Feishu Voice TTS)
**核心功能**：将文本转语音，并通过飞书 `audio` 消息发送给用户。
*   **能力**：`edge-tts` 合成语音，`ffmpeg` 转 Opus（OGG 容器），调用飞书 API 执行“先上传文件、后发送 audio 消息”。
*   **适用场景**：需要在飞书里发送可播放语音，而不是文本或普通附件降级消息。
*   **输出**：飞书语音消息（message_id + file_key 可追踪）。

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill feishu-voice-tts
```

### 8. 知识星球作业点赞统计 (ZSXQ Homework Likes Export)
**核心功能**：统计知识星球作业题下所有学员提交的点赞数，并导出 CSV。
*   **能力**：按作业题抓取学员提交，生成学员汇总表和提交明细表。
*   **适用场景**：课程、训练营、作业打卡活动的点赞统计。
*   **说明文档**：[docs/zsxq-likes-skills.md](docs/zsxq-likes-skills.md)

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-homework-likes-export
```

### 9. 知识星球图文点赞统计 (ZSXQ Tuwen Likes Export)
**核心功能**：从知识星球汇总贴中预览并确认图文链接，再导出点赞明细和按作者汇总 CSV。
*   **能力**：提取同一段/同一行里的“图文 + 知识星球链接”，确认后统计当前点赞数。
*   **适用场景**：图文作业、内容共创、社群投稿的点赞排名统计。
*   **说明文档**：[docs/zsxq-likes-skills.md](docs/zsxq-likes-skills.md)

```bash
npx skills add https://github.com/Tangc/tangzhan-skills --skill zsxq-tuwen-likes-export
```

---

## 🤝 交流与反馈

欢迎加微信 **tcimpk** 交流 Skill 开发经验与使用心得。
