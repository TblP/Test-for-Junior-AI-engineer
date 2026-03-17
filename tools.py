import csv
import os
from typing import Optional

DATA_FILE = os.getenv("CSV_PATH", "financial_data.csv")


def _load_data() -> list[dict]:
    """Загружает CSV и возвращает список строк как dict."""
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-16") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "year": int(row["year"]),
                "revenue": float(row["revenue"]),
                "cogs": float(row["cogs"]),
                "operating_expenses": float(row["operating_expenses"]),
                "net_income": float(row["net_income"]),
            })
    return sorted(rows, key=lambda r: r["year"])


def get_raw_data(year: Optional[int] = None) -> list[dict]:
    """
    Возвращает сырые данные из CSV.
    Если year указан — только за этот год, иначе все годы.
    """
    data = _load_data()
    if year is not None:
        data = [r for r in data if r["year"] == year]
    return data


def get_revenue_growth(year_start: int, year_end: int) -> dict:
    """
    Считает рост выручки между двумя годами.
    Формула: (revenue_end - revenue_start) / revenue_start * 100
    """
    data = {r["year"]: r for r in _load_data()}

    if year_start not in data:
        return {"error": f"Год {year_start} не найден в данных"}
    if year_end not in data:
        return {"error": f"Год {year_end} не найден в данных"}

    rev_start = data[year_start]["revenue"]
    rev_end = data[year_end]["revenue"]
    growth_pct = (rev_end - rev_start) / rev_start * 100

    return {
        "year_start": year_start,
        "year_end": year_end,
        "revenue_start": rev_start,
        "revenue_end": rev_end,
        "revenue_growth_pct": round(growth_pct, 2),
        "formula": f"({rev_end} - {rev_start}) / {rev_start} * 100 = {round(growth_pct, 2)}%",
    }


def get_operating_margin(year: Optional[int] = None) -> list[dict]:
    """
    Считает операционную маржу.
    Формула: (revenue - cogs - operating_expenses) / revenue * 100
    """
    data = _load_data()
    if year is not None:
        data = [r for r in data if r["year"] == year]
        if not data:
            return [{"error": f"Год {year} не найден в данных"}]

    result = []
    for r in data:
        operating_income = r["revenue"] - r["cogs"] - r["operating_expenses"]
        margin = operating_income / r["revenue"] * 100
        result.append({
            "year": r["year"],
            "revenue": r["revenue"],
            "operating_income": operating_income,
            "operating_margin_pct": round(margin, 2),
            "formula": f"({r['revenue']} - {r['cogs']} - {r['operating_expenses']}) / {r['revenue']} * 100 = {round(margin, 2)}%",
        })
    return result


def get_net_margin(year: Optional[int] = None) -> list[dict]:
    """
    Считает чистую маржу.
    Формула: net_income / revenue * 100
    """
    data = _load_data()
    if year is not None:
        data = [r for r in data if r["year"] == year]
        if not data:
            return [{"error": f"Год {year} не найден в данных"}]

    result = []
    for r in data:
        margin = r["net_income"] / r["revenue"] * 100
        result.append({
            "year": r["year"],
            "revenue": r["revenue"],
            "net_income": r["net_income"],
            "net_margin_pct": round(margin, 2),
            "formula": f"{r['net_income']} / {r['revenue']} * 100 = {round(margin, 2)}%",
        })
    return result


def get_summary_metrics() -> list[dict]:
    """
    Возвращает полную таблицу метрик за все годы:
    revenue_growth, operating_margin, net_margin.
    """
    data = _load_data()
    result = []

    for i, r in enumerate(data):
        operating_income = r["revenue"] - r["cogs"] - r["operating_expenses"]
        op_margin = operating_income / r["revenue"] * 100
        net_margin = r["net_income"] / r["revenue"] * 100

        # Рост выручки — год к году (YoY)
        if i == 0:
            yoy_growth = None
        else:
            prev_rev = data[i - 1]["revenue"]
            yoy_growth = round((r["revenue"] - prev_rev) / prev_rev * 100, 2)

        result.append({
            "year": r["year"],
            "revenue": r["revenue"],
            "cogs": r["cogs"],
            "operating_expenses": r["operating_expenses"],
            "net_income": r["net_income"],
            "operating_income": operating_income,
            "operating_margin_pct": round(op_margin, 2),
            "net_margin_pct": round(net_margin, 2),
            "revenue_growth_yoy_pct": yoy_growth,
        })

    return result




def get_fastest_growth_year() -> dict:
    """Находит год с максимальным ростом выручки (YoY)."""
    data = _load_data()
    best = None
    for i in range(1, len(data)):
        prev = data[i - 1]["revenue"]
        curr = data[i]["revenue"]
        growth = (curr - prev) / prev * 100
        if best is None or growth > best["revenue_growth_yoy_pct"]:
            best = {
                "year": data[i]["year"],
                "revenue": curr,
                "prev_year": data[i - 1]["year"],
                "prev_revenue": prev,
                "revenue_growth_yoy_pct": round(growth, 2),
                "formula": f"({curr} - {prev}) / {prev} * 100 = {round(growth, 2)}%",
            }
    return best


def get_best_margin_year(margin_type: str = "net") -> dict:
    """
    Находит год с максимальной маржой.
    margin_type: 'net' — чистая маржа, 'operating' — операционная маржа.
    """
    data = _load_data()
    best = None
    for r in data:
        if margin_type == "operating":
            op_income = r["revenue"] - r["cogs"] - r["operating_expenses"]
            margin = op_income / r["revenue"] * 100
            key = "operating_margin_pct"
        else:
            margin = r["net_income"] / r["revenue"] * 100
            key = "net_margin_pct"

        if best is None or margin > best[key]:
            best = {
                "year": r["year"],
                "revenue": r["revenue"],
                key: round(margin, 2),
                "margin_type": margin_type,
            }
    return best


def get_top_years(metric: str = "revenue", n: int = 3) -> list[dict]:
    """
    Возвращает топ-N лет по заданной метрике.
    metric: 'revenue', 'net_income', 'net_margin', 'operating_margin', 'revenue_growth'
    """
    data = _load_data()
    rows = []
    for i, r in enumerate(data):
        op_income = r["revenue"] - r["cogs"] - r["operating_expenses"]
        yoy = None
        if i > 0:
            yoy = (r["revenue"] - data[i-1]["revenue"]) / data[i-1]["revenue"] * 100

        rows.append({
            "year": r["year"],
            "revenue": r["revenue"],
            "net_income": r["net_income"],
            "net_margin_pct": round(r["net_income"] / r["revenue"] * 100, 2),
            "operating_margin_pct": round(op_income / r["revenue"] * 100, 2),
            "revenue_growth_yoy_pct": round(yoy, 2) if yoy is not None else None,
        })

    metric_map = {
        "revenue": "revenue",
        "net_income": "net_income",
        "net_margin": "net_margin_pct",
        "operating_margin": "operating_margin_pct",
        "revenue_growth": "revenue_growth_yoy_pct",
    }
    sort_key = metric_map.get(metric, "revenue")
    filtered = [r for r in rows if r[sort_key] is not None]
    return sorted(filtered, key=lambda r: r[sort_key], reverse=True)[:n]

# Реестр функций для вызова по имени
TOOL_FUNCTIONS = {
    "get_raw_data": get_raw_data,
    "get_revenue_growth": get_revenue_growth,
    "get_operating_margin": get_operating_margin,
    "get_net_margin": get_net_margin,
    "get_summary_metrics": get_summary_metrics,
    "get_fastest_growth_year": get_fastest_growth_year,
    "get_best_margin_year": get_best_margin_year,
    "get_top_years": get_top_years,
}

# Схема tools для OpenAI API
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_raw_data",
            "description": "Возвращает сырые финансовые данные из CSV. Используй когда нужны исходные цифры по конкретному году или за весь период.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Год (2005-2024). Если не указан — возвращаются все годы.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_revenue_growth",
            "description": "Считает рост выручки между двумя годами в процентах. Используй для анализа динамики выручки.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_start": {"type": "integer", "description": "Начальный год"},
                    "year_end": {"type": "integer", "description": "Конечный год"},
                },
                "required": ["year_start", "year_end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_operating_margin",
            "description": "Считает операционную маржу: (revenue - cogs - operating_expenses) / revenue * 100. Используй для оценки операционной эффективности.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Год (2005-2024). Если не указан — возвращаются все годы.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_net_margin",
            "description": "Считает чистую маржу: net_income / revenue * 100. Используй для оценки итоговой прибыльности.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Год (2005-2024). Если не указан — возвращаются все годы.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary_metrics",
            "description": "Возвращает полную таблицу всех метрик за все годы: выручка, маржи, YoY рост. Используй для общего обзора или сравнительного анализа.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fastest_growth_year",
            "description": "Находит год с максимальным ростом выручки год-к-году. Используй на вопросы типа 'самый быстрый рост', 'лучший год по росту выручки'.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_best_margin_year",
            "description": "Находит год с максимальной маржой. Используй на вопросы типа 'самая высокая прибыльность', 'лучший год по марже'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "margin_type": {
                        "type": "string",
                        "enum": ["net", "operating"],
                        "description": "'net' — чистая маржа, 'operating' — операционная маржа",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_years",
            "description": "Возвращает топ-N лет по выбранной метрике. Используй на вопросы типа 'топ 3 года по выручке', 'лучшие годы по прибыли'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["revenue", "net_income", "net_margin", "operating_margin", "revenue_growth"],
                        "description": "Метрика для сортировки",
                    },
                    "n": {"type": "integer", "description": "Количество лет (по умолчанию 3)"},
                },
                "required": [],
            },
        },
    },
]