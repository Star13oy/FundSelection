from __future__ import annotations

import json
import math
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from time import sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import akshare as ak
except ImportError:  # pragma: no cover - optional at runtime until dependency is installed
    ak = None


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FundSelection/1.0"
_ETF_CACHE: dict[str, dict[str, object]] = {}
_OTC_CACHE: dict[str, dict[str, object]] = {}


@dataclass
class MarketQuote:
    current_price: float | None = None
    previous_close: float | None = None
    intraday_high: float | None = None
    intraday_low: float | None = None
    open_price: float | None = None
    price_change_pct: float | None = None
    price_change_value: float | None = None
    nav: float | None = None
    nav_date: str | None = None
    nav_estimate: float | None = None
    nav_estimate_change_pct: float | None = None
    volume: float | None = None
    turnover: float | None = None
    quote_time: str | None = None
    source: str | None = None
    raw_payload: str | None = None

    def as_db(self) -> dict[str, object]:
        return {
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "intraday_high": self.intraday_high,
            "intraday_low": self.intraday_low,
            "open_price": self.open_price,
            "price_change_pct": self.price_change_pct,
            "price_change_value": self.price_change_value,
            "nav": self.nav,
            "nav_date": self.nav_date,
            "nav_estimate": self.nav_estimate,
            "nav_estimate_change_pct": self.nav_estimate_change_pct,
            "volume": self.volume,
            "turnover": self.turnover,
            "quote_time": self.quote_time,
            "source": self.source,
            "raw_payload": self.raw_payload,
        }


def _to_float(value: object) -> float | None:
    if value in (None, "", "---"):
        return None
    if isinstance(value, str):
        cleaned = value.replace("%", "").replace(",", "").strip()
        if not cleaned:
            return None
        value = cleaned
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def _json_safe(value: object) -> object:
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _safe_json_dumps(value: object) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, default=str, allow_nan=False)


def prepare_market_context() -> None:
    global _ETF_CACHE, _OTC_CACHE

    _ETF_CACHE = {}
    _OTC_CACHE = {}
    if ak is None:
        return

    try:
        etf_df = ak.fund_etf_spot_em()
        _ETF_CACHE = {str(row["代码"]).zfill(6): row.to_dict() for _, row in etf_df.iterrows()}
    except Exception:
        _ETF_CACHE = {}

    try:
        estimation_df = ak.fund_value_estimation_em(symbol="全部")
        _OTC_CACHE = {str(row["基金代码"]).zfill(6): row.to_dict() for _, row in estimation_df.iterrows()}
    except Exception:
        _OTC_CACHE = {}


def clear_market_context() -> None:
    global _ETF_CACHE, _OTC_CACHE
    _ETF_CACHE = {}
    _OTC_CACHE = {}


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            with urlopen(request, timeout=10, context=context) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                sleep(0.4 * (attempt + 1))

    if last_error is None:
        raise RuntimeError("quote fetch failed")
    raise last_error


def _secid_for_etf(code: str) -> str:
    if code.startswith(("5", "6")):
        return f"1.{code}"
    return f"0.{code}"


def _fetch_etf_quote_akshare(code: str) -> MarketQuote | None:
    row = _ETF_CACHE.get(code)
    if not row:
        return None
    return MarketQuote(
        current_price=_to_float(row.get("最新价")),
        previous_close=_to_float(row.get("昨收")),
        intraday_high=_to_float(row.get("最高价")),
        intraday_low=_to_float(row.get("最低价")),
        open_price=_to_float(row.get("开盘价")),
        price_change_pct=_to_float(row.get("涨跌幅")),
        price_change_value=_to_float(row.get("涨跌额")),
        nav_estimate=_to_float(row.get("IOPV实时估值")),
        volume=_to_float(row.get("成交量")),
        turnover=_to_float(row.get("成交额")),
        quote_time=str(row.get("更新时间")) if row.get("更新时间") is not None else None,
        source="AKShare fund_etf_spot_em",
        raw_payload=_safe_json_dumps(row),
    )


def _fetch_otc_quote_akshare(code: str) -> MarketQuote | None:
    row = _OTC_CACHE.get(code)
    if not row:
        return None

    estimate_value_key = next((key for key in row if isinstance(key, str) and key.endswith("-估算数据-估算值")), None)
    estimate_pct_key = next((key for key in row if isinstance(key, str) and key.endswith("-估算数据-估算增长率")), None)
    nav_key = next((key for key in row if isinstance(key, str) and key.endswith("-公布数据-单位净值")), None)
    previous_nav_key = next(
        (
            key
            for key in row
            if isinstance(key, str)
            and key.endswith("-单位净值")
            and "公布数据" not in key
        ),
        None,
    )
    quote_time = estimate_value_key.removesuffix("-估算数据-估算值") if estimate_value_key else None
    nav_date = previous_nav_key.removesuffix("-单位净值") if previous_nav_key else None

    return MarketQuote(
        current_price=_to_float(row.get(estimate_value_key)) if estimate_value_key else None,
        previous_close=_to_float(row.get(nav_key)) if nav_key else None,
        nav=_to_float(row.get(nav_key)) if nav_key else None,
        nav_date=nav_date,
        nav_estimate=_to_float(row.get(estimate_value_key)) if estimate_value_key else None,
        nav_estimate_change_pct=_to_float(row.get(estimate_pct_key)) if estimate_pct_key else None,
        price_change_pct=_to_float(row.get(estimate_pct_key)) if estimate_pct_key else None,
        quote_time=quote_time,
        source="AKShare fund_value_estimation_em",
        raw_payload=_safe_json_dumps(row),
    )


def fetch_etf_quote(code: str, use_fallback: bool = True) -> MarketQuote | None:
    akshare_quote = _fetch_etf_quote_akshare(code)
    if akshare_quote is not None:
        return akshare_quote
    if not use_fallback:
        return None

    params = {
        "secid": _secid_for_etf(code),
        "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f169,f170",
    }
    payload = _fetch_text(f"https://push2.eastmoney.com/api/qt/stock/get?{urlencode(params)}")
    body = json.loads(payload).get("data") or {}
    return MarketQuote(
        current_price=(body.get("f43") or 0) / 100 if body.get("f43") is not None else None,
        intraday_high=(body.get("f44") or 0) / 100 if body.get("f44") is not None else None,
        intraday_low=(body.get("f45") or 0) / 100 if body.get("f45") is not None else None,
        open_price=(body.get("f46") or 0) / 100 if body.get("f46") is not None else None,
        volume=float(body.get("f47")) if body.get("f47") is not None else None,
        turnover=float(body.get("f48")) if body.get("f48") is not None else None,
        previous_close=(body.get("f60") or 0) / 100 if body.get("f60") is not None else None,
        price_change_value=(body.get("f169") or 0) / 100 if body.get("f169") is not None else None,
        price_change_pct=(body.get("f170") or 0) / 100 if body.get("f170") is not None else None,
        quote_time=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        source="Eastmoney Push2 ETF",
        raw_payload=_safe_json_dumps(body),
    )


def fetch_otc_quote(code: str, use_fallback: bool = True) -> MarketQuote | None:
    akshare_quote = _fetch_otc_quote_akshare(code)
    if akshare_quote is not None:
        return akshare_quote
    if not use_fallback:
        return None

    payload = _fetch_text(f"https://fundgz.1234567.com.cn/js/{code}.js")
    body = payload.removeprefix("jsonpgz(").removesuffix(");")
    data = json.loads(body)
    return MarketQuote(
        current_price=float(data["gsz"]) if data.get("gsz") else None,
        previous_close=float(data["dwjz"]) if data.get("dwjz") else None,
        nav=float(data["dwjz"]) if data.get("dwjz") else None,
        nav_date=data.get("jzrq"),
        nav_estimate=float(data["gsz"]) if data.get("gsz") else None,
        nav_estimate_change_pct=float(data["gszzl"]) if data.get("gszzl") else None,
        price_change_pct=float(data["gszzl"]) if data.get("gszzl") else None,
        quote_time=data.get("gztime"),
        source="Eastmoney Fund GZ",
        raw_payload=_safe_json_dumps(data),
    )
