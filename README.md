# 微信聊天记录分析工具（单文件版）

输入一个 chatlog API URL，自动完成数据下载、格式化、全量统计分析，并生成供智能体执行的心理测评任务包。

## 环境要求

- Python 3.8+

安装依赖：

```bash
pip install jieba pandas openpyxl requests
```

## 使用方法

```bash
python main.py "http://127.0.0.1:5030/api/v1/chatlog?limit=100000"
```

- 参数：`<URL>`（chatlog API 地址，也支持本地 JSON 文件路径）、`-o` 输出目录（默认 `output`）、`--timeout` 下载超时秒数
- URL 含 `&` 等特殊字符时请用引号包裹
- 如聊天记录不全，请在 URL 中加大 `limit` 参数

## 输出文件（默认 ./output）

| 文件 | 说明 |
|------|------|
| `chat_format.json` | 格式化后的聊天记录 |
| `chat_analysis.xlsx` | 全量统计（语音电话、常用词TOP50、聊天数最高10日、24小时/周/月趋势、周/月消息频次、消息月占比） |
| `assessment_tasks.json` | 心理测评任务包（按周分批，含子智能体所需完整提示词与聊天记录） |
| `run_summary.json` | 运行摘要（各阶段状态与统计概要，供主智能体监测统计过程） |

## 智能体协作（心理测评）

心理测评不再由脚本直接调用 LLM API，而是由智能体完成：

1. **主智能体（监测与调度）**：运行本脚本，读取 `run_summary.json` 监测统计过程；
2. **子智能体（心理测评）**：读取 `assessment_tasks.json`，逐个执行 `tasks` 中的测评任务（每个任务包含 `system_prompt`、`user_prompt` 和完整聊天记录），按 `result_file_suggestion` 保存测评报告；
3. 主智能体收集各批次报告，汇总为最终心理测评总报告。

## 输入数据格式

chatlog API 返回的消息字段：`time`（ISO 时间）、`isSelf`、`senderName`、`type`、`content`。

消息类型映射：1 文本 / 3 图片 / 34 语音 / 43 视频 / 47 表情 / 49 引用或转发 / 50、11000 语音电话 / 10000 撤回。
