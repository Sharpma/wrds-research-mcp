from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResearchRequest:
    original_text: str
    dataset: str
    company: str
    ticker: str
    start_date: date
    end_date: date
    frequency: str
    fields: list[str]
    output_format: str = "parquet"

    def as_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "dataset": self.dataset,
            "company": self.company,
            "ticker": self.ticker,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "frequency": self.frequency,
            "fields": self.fields,
            "output_format": self.output_format,
        }


@dataclass(frozen=True)
class SecurityIdentifier:
    ticker: str
    permno: int
    company_name: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "permno": self.permno,
            "company_name": self.company_name,
            "source": self.source,
        }


@dataclass(frozen=True)
class QueryPlan:
    sql: str
    params: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "sql": self.sql,
            "params": self.params,
        }


@dataclass(frozen=True)
class MaterializedDataset:
    output_path: Path
    metadata_path: Path
    row_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_path": str(self.output_path),
            "metadata_path": str(self.metadata_path),
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class PipelineResult:
    request: ResearchRequest
    security: SecurityIdentifier
    query_plan: QueryPlan
    dataset: MaterializedDataset
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.as_dict(),
            "security": self.security.as_dict(),
            "query_plan": self.query_plan.as_dict(),
            "dataset": self.dataset.as_dict(),
            "source": self.source,
        }
