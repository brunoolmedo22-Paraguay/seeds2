# H₂V · Energy Management System

Aplicação Streamlit unificada para monitoramento do sistema solar–bateria–hidrogênio. Esta primeira versão conecta os dois modelos científicos já existentes:

- modelo fotovoltaico Single Diode Model (SDM), com MPP e temperatura NOCT;
- modelo PEMFC Horizon VLIIPro50-22 aproximado, com stack equivalente de 65–66 kW, balance of plant, inversão de potência, estados e rampas.

A bateria e o otimizador já possuem espaços definidos na interface, mas ainda não contêm seus modelos definitivos.

## Estrutura da interface

1. **Visão geral** — KPIs, curvas integradas e dona de participação energética;
2. **Entradas** — leitura por CSV, escolha da hora inicial e janela fixa de 120 minutos;
3. **Modelos** — entradas, saídas, parâmetros e gráficos individuais;
4. **Otimizador** — estrutura reservada para o otimizador da Marília;
5. **Configurações** — estrutura reservada para cenários e cargas.

## Rodar localmente

Requer Python 3.12.

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Community Cloud

1. Extraia o ZIP e envie **o conteúdo da pasta** para a raiz do repositório GitHub.
2. Confirme que `app.py`, `requirements.txt`, `runtime.txt`, `ems_app/` e `ems_core/` estão na raiz.
3. No Streamlit Community Cloud, selecione o repositório e defina `app.py` como arquivo principal.
4. Não é necessário configurar secrets nesta versão.

## Contrato mínimo de entrada

O parser aceita CSV separado por vírgula ou ponto e vírgula. Colunas mínimas:

| Coluna | Unidade | Uso |
|---|---:|---|
| `timestamp` | data/hora | eixo temporal comum |
| `irradiancia_W_m2` | W/m² | entrada do modelo FV |
| `temperatura_ambiente_C` | °C | entrada FV e condição da PEMFC |
| `potencia_solicitada_fc_kW` | kW | referência de potência da PEMFC |

Colunas opcionais: `carga_total_kW`, `FC_enable`, `T_coolant_in_C` e `V_bus_V`.

O arquivo [`data/entrada_padrao_ems.csv`](data/entrada_padrao_ems.csv) pode ser usado para teste imediato.

### Janela operacional

- o arquivo padrão contém 24 horas e 1.440 registros, um por minuto;
- o usuário escolhe a hora inicial na aba **Entradas**;
- a app recorta exatamente 120 pontos com resolução de 1 minuto;
- selecionar `15:00` produz a janela `15:00 → 17:00`, com timestamps entre `15:00` e `16:59`;
- o arranjo FV inicial é `2 módulos em série × 3 strings em paralelo`;
- a PEMFC é integrada a cada 60 segundos nesta interface.

## Sinais sintéticos

Carga e bateria começam desativadas. Quando a opção **Simular carga e bateria ainda indisponíveis** é ativada, a aplicação gera carga total, potência de bateria e SOC apenas para validar o dashboard. Esses sinais não constituem um modelo de bateria e não são usados para modificar as respostas FV ou PEMFC.

## Próximas integrações

- modelo físico da bateria;
- otimizador de despacho da Marília;
- modelo do motor/propulsão, permitindo monitorar velocidade, potência e consumo;
- leitura automática por API.

## Observação científica sobre a PEMFC

O perfil PEMFC é `EQUIVALENT_65KW_HORIZON_CONSTRAINED`. Ele é adequado para estudos preliminares de EMS, mas ainda não representa validação experimental do equipamento Horizon instalado na embarcação. Consulte `docs/MODEL_CARD_HORIZON_APPROX.md` e `docs/METODOLOGIA_MODELO_HORIZON_APROX.md`.
