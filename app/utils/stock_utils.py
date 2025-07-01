import re


def extract_stock_info(info):
    # 日本語企業概要の取得
    summary = info.get("longBusinessSummary")
    if summary and "。" in summary:
        summary = summary.split("。", 1)[0] + "。"
    # 従業員数カンマ区切り
    employees = info.get("fullTimeEmployees")
    if employees is not None:
        employees = f"{employees:,}"
    return {
        "銘柄名": info.get("longName") or info.get("shortName"),
        "市場": info.get("exchange"),
        "symbol": info.get("symbol"),
        "現在値": info.get("regularMarketPrice"),
        "前日終値": info.get("regularMarketPreviousClose"),
        "始値": info.get("regularMarketOpen"),
        "高値": info.get("regularMarketDayHigh"),
        "安値": info.get("regularMarketDayLow"),
        "出来高": info.get("regularMarketVolume"),
        "時価総額": info.get("marketCap"),
        "PER": info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "配当利回り": info.get("dividendYield"),
        "52週高値": info.get("fiftyTwoWeekHigh"),
        "52週安値": info.get("fiftyTwoWeekLow"),
        "業種": info.get("industry"),
        "本社所在地": info.get("city"),
        "従業員数": employees,
        "企業概要": summary,
    }


def normalize_jp_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    # 4桁数字のみなら.Tを付与
    if re.fullmatch(r"\d{4}", symbol):
        return symbol + ".T"
    # 既に.T付きならそのまま
    if symbol.endswith(".T"):
        return symbol
    # それ以外はエラー
    raise ValueError("日本株は4桁コードまたは4桁+.Tで入力してください")
