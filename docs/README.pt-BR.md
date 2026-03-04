# Amazon Sales Analysis (PT-BR)

## Troca de Idioma
- README principal: [../README.md](../README.md)
- English: [README.en.md](README.en.md)

## Resumo Executivo
- Problema de negocio: leakage de receita por descontos.
- Publico-alvo: lideranca comercial, Revenue Ops e gestores de categoria.
- North Star Metric: Net Revenue Retained (NRR).
- Potencial financeiro: +$252,3K ao recuperar 5% do leakage.

## Metricas de Negocio
- Receita Liquida: **$32,87M**
- Leakage de Desconto: **$5,05M**
- North Star (NRR): **86,69%**
- Upside com 5% de recuperacao: **+$252,3K**

## Sumario
- [Visao do Projeto](#visao-do-projeto)
- [Diferenciais para Recrutadores e Leads](#diferenciais-para-recrutadores-e-leads)
- [Fonte do Dataset](#fonte-do-dataset)
- [Executar Localmente](#executar-localmente)
- [Qualidade e Contratos](#qualidade-e-contratos)
- [CI e Metricas de Produto](#ci-e-metricas-de-produto)
- [Processo de Release](#processo-de-release)
- [Stack](#stack)
- [Contato](#contato)

## Visao do Projeto
Este projeto demonstra um fluxo completo de dados aplicado a vendas da Amazon:
- ingestao automatizada via Kaggle Hub;
- limpeza com regras de consistencia;
- analise exploratoria e visualizacoes executivas;
- dashboard Streamlit com foco em decisao e storytelling de negocio.

## Diferenciais para Recrutadores e Leads
- Estrutura em camadas, orientada a manutencao.
- Pipeline reproduzivel (`scripts/run_pipeline.py`).
- Qualidade de dados validada por testes.
- App com filtros de negocio e metricas acionaveis.

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
```

## Qualidade e Contratos
- Contrato do dataset bruto: `contracts/sales_dataset.contract.json`
- Contrato de metricas: `contracts/product_metrics.contract.json`
- Gates no pipeline:
  - validacao de esquema de entrada
  - validacoes de dominio no dataset limpo
  - geracao de metricas em `reports/metrics/product_metrics.json`

### Comandos de Qualidade
```bash
pip install -r requirements-dev.txt
black --check .
isort --check-only .
ruff check .
mypy src scripts
pytest
```

## CI e Metricas de Produto
- Workflow: `.github/workflows/ci.yml`
- Gates: formatacao, lint, tipagem, testes e cobertura (`>=70%`)
- Artefatos de CI:
  - `reports/metrics/coverage.xml`
  - `reports/metrics/pytest-results.xml`

## Processo de Release
1. Atualizar o `CHANGELOG.md` com a nova versao.
2. Atualizar versao:
   ```bash
   python scripts/bump_version.py 0.2.0
   ```
3. Criar tag e enviar:
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```
4. O workflow `.github/workflows/release.yml` valida coerencia de versao/changelog e publica o release.

## Stack
Python, Pandas, Plotly, Streamlit, Seaborn, Matplotlib, Pytest.

## Contato
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com



