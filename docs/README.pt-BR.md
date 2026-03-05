# Amazon Sales Analysis (PT-BR)

## Troca de Idioma
- README principal: [../README.md](../README.md)
- English: [README.en.md](README.en.md)

## Resumo Executivo
- Problema de negócio: leakage de receita por descontos.
- Público-alvo: liderança comercial, Revenue Ops e gestores de categoria.
- North Star Metric: Net Revenue Retained (NRR).
- Potencial financeiro: +$252,3K ao recuperar 5% do leakage.

## Métricas de Negócio
- Receita Líquida: **$32,87M**
- Leakage de Desconto: **$5,05M**
- North Star (NRR): **86,69%**
- Upside com 5% de recuperação: **+$252,3K**

## Sumário
- [Visão do Projeto](#visão-do-projeto)
- [Diferenciais para Recrutadores e Leads](#diferenciais-para-recrutadores-e-leads)
- [Fonte do Dataset](#fonte-do-dataset)
- [Executar Localmente](#executar-localmente)
- [Qualidade e Contratos](#qualidade-e-contratos)
- [CI e Métricas de Produto](#ci-e-métricas-de-produto)
- [Processo de Release](#processo-de-release)
- [Cadência de Decisão](#cadência-de-decisão)
- [Stack](#stack)
- [Contato](#contato)

## Visão do Projeto
Este projeto demonstra um fluxo completo de dados aplicado a vendas da Amazon:
- ingestão automatizada via Kaggle Hub;
- limpeza com regras de consistência;
- análise exploratória e visualizações executivas;
- dashboard Streamlit com foco em decisão e storytelling de negócio;
- simulador de cenários por categoria para recuperação de leakage;
- detecção de anomalias de picos de desconto com export de alertas;
- API FastAPI para expor métricas e alertas para integração com BI.

## Diferenciais para Recrutadores e Leads
- Estrutura em camadas, orientada à manutenção.
- Pipeline reproduzível (`scripts/run_pipeline.py`).
- Qualidade de dados validada por testes.
- App com filtros de negócio e métricas acionáveis.

## Fonte do Dataset
- Kaggle: `aliiihussain/amazon-sales-dataset`
- Link: https://www.kaggle.com/datasets/aliiihussain/amazon-sales-dataset

## Executar Localmente
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_pipeline.py
streamlit run app/streamlit_app.py
uvicorn app.api:app --reload
```

## Qualidade e Contratos
- Contrato do dataset bruto: `contracts/sales_dataset.contract.json`
- Contrato de métricas: `contracts/product_metrics.contract.json`
- Gates no pipeline:
  - validação de esquema de entrada
  - validações de domínio no dataset limpo
  - geração de métricas em `reports/metrics/product_metrics.json`
  - export de alertas em `reports/tables/discount_spike_alerts.csv`

### Comandos de Qualidade
```bash
pip install -r requirements-dev.txt
black --check .
isort --check-only .
ruff check .
mypy src scripts
pytest
```

## CI e Métricas de Produto
- Workflow: `.github/workflows/ci.yml`
- Gates: formatação, lint, tipagem, testes e cobertura (`>=70%`)
- Artefatos de CI:
  - `reports/metrics/coverage.xml`
  - `reports/metrics/pytest-results.xml`

## Processo de Release
1. Atualizar o `CHANGELOG.md` com a nova versão.
2. Atualizar versão:
   ```bash
   python scripts/bump_version.py 0.2.0
   ```
3. Criar tag e enviar:
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```
4. O workflow `.github/workflows/release.yml` valida coerência de versão/changelog e publica o release.

## Cadência de Decisão
- Semanal: acompanhar `north_star_nrr` e `discount_leakage`, revisando os alertas de `reports/tables/discount_spike_alerts.csv`.
- Mensal: revisar e recalibrar thresholds de desconto por categoria com base no Scenario Simulator.

## Stack
Python, Pandas, Plotly, Streamlit, FastAPI, Seaborn, Matplotlib, Pytest.

## Contato
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com



