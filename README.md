# Financial Analyst API

FastAPI-сервис для анализа финансовых данных компании с использованием LLM через function calling.  
Подключается к Open WebUI как кастомная OpenAI-совместимая модель.

---

## Архитектура

```
Open WebUI
    │
    │  POST /v1/chat/completions
    ▼
FastAPI (main.py)
    │  - убирает системный промпт Open WebUI
    │  - добавляет свой системный промпт
    │  - передаёт запрос + tools schema в LLM
    ▼
LLM (Ollama / OpenRouter)
    │  - понимает вопрос пользователя
    │  - решает какой инструмент вызвать
    │  - возвращает tool_call
    ▼
tools.py (расчёты по CSV)
    │  - выполняет функцию с реальными данными
    │  - возвращает точные цифры + формулы
    ▼
LLM (второй вызов)
    │  - получает реальные данные из инструмента
    │  - формулирует финальный ответ
    ▼
Open WebUI — показывает ответ пользователю
```

**Ключевая идея:** LLM никогда не считает сама — она только вызывает Python-функции и интерпретирует их результаты. Это исключает галлюцинации с числами.

---

## Структура проекта

```
financial-analyst/
├── main.py                # FastAPI сервис, OpenAI-совместимый прокси
├── tools.py               # Функции расчёта метрик по CSV
├── financial_data.csv     # Финансовые данные компании за 2005–2024
├── .env                   # Конфигурация (не коммитить в git)
├── .env.example           # Пример конфигурации
└── requirements.txt       # Зависимости
```

---

## Доступные инструменты (tools)

| Функция | Описание |
|---|---|
| `get_raw_data(year?)` | Сырые данные из CSV за год или за весь период |
| `get_revenue_growth(year_start, year_end)` | Рост выручки между двумя годами в % |
| `get_operating_margin(year?)` | Операционная маржа: `(revenue - cogs - opex) / revenue * 100` |
| `get_net_margin(year?)` | Чистая маржа: `net_income / revenue * 100` |
| `get_summary_metrics()` | Полная таблица всех метрик за все годы |
| `get_fastest_growth_year()` | Год с максимальным ростом выручки YoY |
| `get_best_margin_year(margin_type)` | Год с максимальной чистой или операционной маржой |
| `get_top_years(metric, n)` | Топ-N лет по выбранной метрике |

---

## Установка

```bash
# Клонируем или копируем файлы проекта
cd financial-analyst

# Создаём виртуальное окружение
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Устанавливаем зависимости
pip install -r requirements.txt
```

---

## Конфигурация

```bash
cp .env.example .env
```

Открой `.env` и заполни:

```env
# Для Ollama (локально)
OPENROUTER_API_KEY=ollama
OPENROUTER_BASE_URL=http://localhost:11434/v1
MODEL=llama3.1:8b

# Для OpenRouter (облако)
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=google/gemini-flash-1.5

# Путь к CSV файлу
CSV_PATH=financial_data.csv
```

### Рекомендуемые модели

| Модель | Провайдер | Function calling |
|---|---|---|
| `llama3.1:8b` | Ollama | ✅ Хорошо |
| `qwen2.5:7b` | Ollama | ✅ Отлично |
| `llama3.2:3b` | Ollama | ⚠️ Нестабильно |
| `google/gemini-flash-1.5` | OpenRouter | ✅ Хорошо |
| `anthropic/claude-3-haiku` | OpenRouter | ✅ Отлично |

---

## Запуск

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Проверка что сервис работает:

```bash
curl http://localhost:8000/
# {"status":"ok","service":"Financial Analyst API"}

curl http://localhost:8000/v1/models
# {"object":"list","data":[{"id":"financial-analyst",...}]}
```

---

## Подключение к Open WebUI

1. Open WebUI → **Settings → Connections**
2. Добавить новый OpenAI-совместимый endpoint:
   - **URL**: `http://<IP_сервера>:8000/v1`
   - **API Key**: любая строка (например `dummy`)
3. В чате выбрать модель **financial-analyst**

---

## Примеры вопросов

- "В каком году был самый быстрый рост выручки?"
- "Какая была чистая маржа в 2020 году?"
- "Сравни операционную маржу в 2010 и 2024"
- "Топ 3 года по чистой прибыли"
- "В каком году была самая высокая операционная маржа?"
- "Покажи все метрики за 2015–2020"
- "Дай общий обзор финансовых показателей компании"

---

## Зависимости

```
fastapi==0.115.0      # веб-фреймворк
uvicorn==0.30.6       # ASGI сервер
openai==1.54.0        # OpenAI-совместимый клиент (работает с Ollama и OpenRouter)
python-dotenv==1.0.1  # загрузка .env файла
```
