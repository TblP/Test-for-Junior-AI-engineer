import json
import os
import time
from typing import List, Optional

import openai
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from tools import TOOLS_SCHEMA, TOOL_FUNCTIONS

load_dotenv()
import os
print(">>> API KEY:", os.getenv("OPENROUTER_API_KEY"))
client = openai.OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("MODEL", "hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q5_K_M")

SYSTEM_PROMPT = """Ты — финансовый аналитик. Твоя задача — отвечать на вопросы о финансовых показателях компании за период 2005–2024.

СТРОГИЕ ПРАВИЛА:
1. Никогда не придумывай числовые значения. Все цифры — только из результатов вызванных инструментов.
2. Перед ответом всегда вызывай подходящий инструмент для получения данных.
3. В ответе объясняй формулу расчёта если она была применена.
4. Структурируй ответ: сначала вывод, затем детали с цифрами.
5. Если данных за запрошенный период нет — честно сообщи об этом.

Доступные метрики:
- Выручка (revenue)
- Себестоимость (cogs)
- Операционные расходы (operating_expenses)
- Чистая прибыль (net_income)
- Операционная маржа = (revenue - cogs - operating_expenses) / revenue * 100
- Чистая маржа = net_income / revenue * 100
- Рост выручки = (revenue_end - revenue_start) / revenue_start * 100
"""

app = FastAPI(title="Financial Analyst API")


# ---------- Pydantic models ----------

class Message(BaseModel):
    role: str
    content: Optional[str] = None


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]


# ---------- Tool calling logic ----------

def _call_tool(name: str, arguments: dict) -> str:
    if name not in TOOL_FUNCTIONS:
        return json.dumps({"error": f"Инструмент '{name}' не найден"})
    try:
        import inspect
        fn = TOOL_FUNCTIONS[name]
        valid_params = inspect.signature(fn).parameters
        # Фильтруем только валидные аргументы и убираем None
        filtered = {k: v for k, v in arguments.items() if k in valid_params and v is not None}
        result = fn(**filtered)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _chat_with_tools(user_messages: list[dict]) -> str:
    """
    Полный цикл с function calling через openai SDK.
    Возвращает финальный текстовый ответ.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages

    for _ in range(10):  # защита от бесконечного цикла
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

        # Финальный ответ — возвращаем
        if choice.finish_reason == "stop" or not message.tool_calls:
            return message.content or ""

        # LLM вызвала инструменты — выполняем и добавляем результаты
        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"
            try:
                fn_args = json.loads(raw_args)
                if not isinstance(fn_args, dict):
                    fn_args = {}
            except json.JSONDecodeError:
                fn_args = {}
            tool_result = _call_tool(fn_name, fn_args)
            print(f"[TOOL] {fn_name}({fn_args}) => {tool_result[:200]}")
            print(f"[TOOL] {fn_name}({fn_args}) => {tool_result[:200]}", flush=True)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

    return "Не удалось получить ответ после нескольких итераций."


# ---------- Endpoints ----------

@app.get("/")
def root():
    return {"status": "ok", "service": "Financial Analyst API"}


@app.get("/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "financial-analyst",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            }
        ],
    }


@app.post("/chat/completions")
def chat_completions(req: ChatRequest):
    # Берём историю сообщений, убираем системный промпт от Open WebUI
    user_messages = [
        {"role": m.role, "content": m.content}
        for m in req.messages
        if m.role != "system"
    ]

    answer = _chat_with_tools(user_messages)

    return {
        "id": "chatcmpl-financial-analyst",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
