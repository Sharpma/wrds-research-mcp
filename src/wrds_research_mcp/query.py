from __future__ import annotations

from wrds_research_mcp.models import QueryPlan, ResearchRequest, SecurityIdentifier


def build_crsp_daily_returns_query(
    request: ResearchRequest,
    security: SecurityIdentifier,
    max_rows: int,
) -> QueryPlan:
    sql = """
select
    d.dlycaldt as date,
    d.permno,
    sn.ticker,
    d.dlyret::double precision as ret,
    d.dlyretx::double precision as retx,
    abs(d.dlyprc)::double precision as prc,
    d.dlyvol::bigint as vol
from crsp.stkdlysecuritydata as d
join crsp.stocknames_v2 as sn
    on d.permno = sn.permno
    and d.dlycaldt between sn.namedt and coalesce(sn.nameenddt, date '9999-12-31')
where d.permno = %(permno)s
    and sn.ticker = %(ticker)s
    and d.dlycaldt between %(start_date)s and %(end_date)s
order by d.dlycaldt
limit %(max_rows)s
""".strip()

    return QueryPlan(
        sql=sql,
        params={
            "permno": security.permno,
            "ticker": security.ticker,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "max_rows": max_rows,
        },
        dataset=request.dataset,
        tables=["crsp.stkdlysecuritydata", "crsp.stocknames_v2"],
        fields=["date", "permno", "ticker", "ret", "retx", "prc", "vol"],
        template_id="crsp_daily_returns_v2",
    )
