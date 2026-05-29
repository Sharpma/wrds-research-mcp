CATALOG = {
    "crsp_daily_returns": {
        "label": "CRSP daily stock returns",
        "tables": ["crsp.dsf", "crsp.stocknames"],
        "frequency": "daily",
        "identifiers": ["ticker", "permno"],
        "fields": {
            "date": "Trading date",
            "permno": "CRSP permanent security identifier",
            "ticker": "Ticker symbol",
            "ret": "Daily total return, stored as decimal",
            "retx": "Daily return excluding dividends, stored as decimal",
            "prc": "Closing price, absolute value",
            "vol": "Trading volume",
        },
    }
}
