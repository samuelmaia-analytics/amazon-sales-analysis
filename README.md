# Amazon Sales Analytics Platform

> **Projeto legado de portfólio.** Este repositório foi preservado como histórico técnico. O portfólio principal atual está concentrado em [Governed Analytics Platform](https://github.com/samuelmaia-analytics/Governed-Analytics-Platform), Central de Automação e Operações e [AWS Serverless Access Counter](https://github.com/samuelmaia-analytics/aws-serverless-access-counter).

Projeto de portfólio em **Data Analytics e Analytics Engineering** focado em desempenho comercial, qualidade de dados e confiabilidade operacional.

A proposta é transformar dados públicos de vendas em um fluxo analítico reproduzível, com camadas de dados, validações, métricas, histórico de execuções e consumo por API, CLI e Streamlit.

## O problema

Análises comerciais recorrentes precisam responder perguntas como:

- Quais categorias e produtos concentram receita?
- Onde há maior pressão de descontos?
- As métricas permanecem estáveis entre execuções?
- Os dados estão confiáveis antes de serem publicados?
- Existe rastreabilidade suficiente para investigar uma execução?

## A solução

```text
Raw
 → validação de contrato e schema
 → Bronze
 → limpeza e normalização
 → Data Quality
 → Silver
 → modelagem de vendas
 → Gold / DuckDB
 → KPIs e regressão
 → API / CLI / Streamlit
```

## Principais entregas

- Pipeline local-first com camadas Bronze, Silver e Gold.
- Contratos e validações de schema antes do processamento.
- Quality Gates sobre dados curados.
- Pacote de KPIs comerciais e comparação entre execuções.
- Materialização analítica em DuckDB.
- Histórico de runs, manifests e status operacionais.
- API para métricas, qualidade, alertas e histórico do pipeline.
- Dashboard Streamlit para consumo dos resultados.
- Testes automatizados e validação em CI.

## Valor demonstrado

O projeto mostra como evoluir uma análise de vendas além de um notebook isolado: métricas ficam reproduzíveis, execuções deixam evidências, inconsistências podem ser detectadas antes do consumo e diferentes interfaces reutilizam a mesma lógica analítica.

## Stack

**Dados:** Python, pandas, SQL, DuckDB  
**Serving:** Streamlit, FastAPI, CLI  
**Qualidade:** contratos, quality gates, pytest, mypy, Ruff, Black, Isort  
**Engenharia:** GitHub Actions, manifests, run history, atomic writes

## Fonte de dados

Dataset público do Kaggle: `aliiihussain/amazon-sales-dataset`.

## Como revisar este projeto em 5 minutos

1. Leia o problema e o fluxo acima.
2. Explore `src/amazon_sales_analysis/` para a lógica principal.
3. Veja as validações e contratos de dados.
4. Execute o pipeline e consulte o histórico de runs.
5. Abra o Streamlit ou a API para visualizar os outputs publicados.

## Execução rápida

```bash
python -m pip install -e .[dev]
PYTHONPATH=src python -m amazon_sales_analysis.cli.pipeline --retention-runs 60
uvicorn app.api:app --reload
streamlit run streamlit_app.py
```

## Qualidade

```bash
make quality
make test
make build-check
```

## Limitações

- Arquitetura intencionalmente local-first.
- Sem orquestrador externo obrigatório.
- Sem armazenamento cloud obrigatório.
- Observabilidade centralizada e estratégia incremental completa estão fora do escopo atual.

## Documentação

- [Estrutura do repositório](docs/REPOSITORY_STRUCTURE.md)
- [Guia PT-BR](docs/README.pt-BR.md)
- [Contribuição](CONTRIBUTING.md)

## Autor

Samuel Maia — Analista de Dados | Analytics Engineer

- LinkedIn: https://www.linkedin.com/in/samuelmaia-analytics/
- GitHub: https://github.com/samuelmaia-analytics

## Licença

Consulte o arquivo [LICENSE](LICENSE).
