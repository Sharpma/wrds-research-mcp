from __future__ import annotations

from wrds_research_mcp.models import QueryPlan, ResearchRequest, SecurityIdentifier


def build_crsp_daily_returns_query(
    request: ResearchRequest,
    security: SecurityIdentifier,
) -> QueryPlan:
    sql = """
select
    d.date,
    d.permno,
    sn.ticker,
    d.ret,
    d.retx,
    abs(d.prc) as prc,
    d.vol
from crsp.dsf as d
join crsp.stocknames as sn
    on d.permno = sn.permno
    and d.date between sn.namedt and coalesce(sn.nameendt, date '9999-12-31')
where d.permno = %(permno)s
    and sn.ticker = %(ticker)s
    and d.date between %(start_date)s and %(end_date)s
order by d.date
""".strip()

    return QueryPlan(
        sql=sql,
        params={
            "permno": security.permno,
            "ticker": security.ticker,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        },
    )
