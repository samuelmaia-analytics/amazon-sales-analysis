# Amazon Sales Analysis (PT-BR)

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

## Stack
Python, Pandas, Plotly, Streamlit, Seaborn, Matplotlib, Pytest.

## Contato
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com
