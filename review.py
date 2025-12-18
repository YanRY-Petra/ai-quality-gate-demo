import json
import os
import sys
from typing import Any, Dict

import requests


# TODO: 在这里填写你的 DeepSeek API Key
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# DeepSeek Chat Completions API 端点（如有变更，请根据官方文档更新）
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def build_prompt(app_code: str) -> str:
    """
    构造发给 DeepSeek 的提示词。

    要求 AI 仅返回 JSON，包含：
      - score: 0-100 的整数分数
      - error_reason: 字符串，指出主要问题 / 风险
      - fix_suggestion: 字符串，给出修复建议
    """
    prompt = f"""
你是一名严格的高级代码审查工程师。现在有一个 Python 脚本 `app.py`，需要你从以下维度进行整体质量评估：
1. 代码是否健壮，是否存在明显 bug 或异常情况未处理
2. 是否遵循 Python 最佳实践和可读性规范
3. 安全性、错误处理、日志等方面是否合理

下面是完整的 app.py 源代码（用 ```python ``` 包裹）：

```python
{app_code}
```

请你综合上述维度，对该代码进行 0-100 打分，并只用严格的 JSON 返回结果，不要包含任何多余文字或注释，不要使用 Markdown。

JSON 结构必须为：
{{
  "score": 0-100 的整数,
  "error_reason": "简要说明你给出这个分数的主要原因，可以包含多个问题的总结",
  "fix_suggestion": "给出可以直接执行的、尽量具体的修复或改进建议"
}}

重要要求：
- 只返回一行合法的 JSON
- 不要在 JSON 外围添加任何文本、换行或者 Markdown 标记
"""
    return prompt.strip()


def call_deepseek(prompt: str) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError(
            "DeepSeek API Key 未设置。请设置环境变量 DEEPSEEK_API_KEY 或在 review.py 中填写 API_KEY。"
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"DeepSeek 返回格式异常: {data}") from exc

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek 返回的内容不是合法 JSON: {content}") from exc

    return result


def main() -> None:
    app_path = os.path.join(os.getcwd(), "app.py")

    if not os.path.isfile(app_path):
        print(f"未找到 app.py 文件: {app_path}", file=sys.stderr)
        sys.exit(1)

    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    prompt = build_prompt(app_code)

    try:
        result = call_deepseek(prompt)
    except Exception as e:  # noqa: BLE001
        print(f"调用 DeepSeek API 失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 兼容 score 是字符串或数字的情况
    score = result.get("score")
    try:
        score_value = int(score)
    except (TypeError, ValueError):
        print(f"返回的 score 非法: {score!r}", file=sys.stderr)
        sys.exit(1)

    error_reason = result.get("error_reason", "")
    fix_suggestion = result.get("fix_suggestion", "")

    # 在控制台打印完整的 JSON 结果，方便调试/记录
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 核心逻辑：分数低于 80 视为失败
    if score_value < 80:
        # 可以额外提示一下原因
        print(
            f"代码审查未通过，得分 {score_value} (< 80)。\n原因: {error_reason}\n建议: {fix_suggestion}",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()


