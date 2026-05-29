CATALOG = {
    "crsp_daily_returns": {
        "label": "CRSP daily stock returns",
        "tables": ["crsp.stkdlysecuritydata", "crsp.stocknames_v2"],
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
    },
    "crsp_monthly_returns": {
        "label": "CRSP monthly stock returns",
        "tables": ["crsp.stkmthsecuritydata"],
        "frequency": "monthly",
        "identifiers": ["ticker", "permno"],
        "fields": {
            "date": "Monthly calendar date",
            "permno": "CRSP permanent security identifier",
            "ticker": "Ticker symbol",
            "ret": "Monthly total return, stored as decimal",
            "retx": "Monthly return excluding dividends, stored as decimal",
            "prc": "Month-end price, absolute value",
            "vol": "Monthly trading volume",
        },
    },
}
