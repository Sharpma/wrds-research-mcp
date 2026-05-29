# wrds-research-mcp

Natural-language access layer for WRDS research data.

This repository is being prepared to support workflows such as requesting
CRSP data in plain language and producing analysis-ready Parquet outputs.

Initial scope: repository setup only.

## 中文说明

`wrds-research-mcp` 的目标是提供一个面向 WRDS 研究数据的自然语言访问层。
未来它将支持类似“获取 2025 年 1 月苹果公司日度收益率数据”的请求，
自动识别数据源、查询 CRSP 等 WRDS 数据库，并整理为可直接分析使用的
Parquet 数据文件。

当前阶段仅完成仓库初始化与远端连接配置，暂不包含 WRDS 或 MCP 功能实现。
