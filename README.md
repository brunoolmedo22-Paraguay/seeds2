# SEED2 · H₂V Energy Management System

Plataforma Streamlit unificada para executar, comparar e monitorar os modelos
energéticos da embarcação H₂V sobre **uma única entrada temporal**.

Esta versão incorpora integralmente o motor `Solar MultiModel` à arquitetura do
SEED2. O bloco fotovoltaico executa automaticamente três estimadores em paralelo;
a mesma janela alimenta a PEMFC/H₂ preliminar e, quando ativada, a camada
sintética de bateria.

## O que está integrado

### Solar · três estimadores automáticos

1. **Irradiância** — linha de continuidade proporcional a `GHI` e à potência STC;
2. **NOCT + eficiência** — acrescenta temperatura de célula e derating térmico;
3. **Single Diode Model (SDM)** — resolve o circuito equivalente e o MPP minuto a minuto.

Os três usam o mesmo timestamp, GHI, temperatura, datasheet, arranjo e perdas.
O resultado operacional prioriza automaticamente `SDM → NOCT → Irradiância`,
sem descartar as demais curvas da comparação.

### PEMFC / H₂

Mantém o modelo Horizon VLIIPro50-22 aproximado, com stack equivalente de
65–66 kW, balance of plant, rampas, estados e consumo de H₂. É uma camada para
estudos preliminares de EMS, ainda sem validação experimental definitiva da
embarcação. Quando a referência de potência é gerada pela aplicação, sua origem
é identificada como sintética.

### Bateria

O modelo físico ainda não está integrado. A aplicação pode gerar potência e SOC
sintéticos para validar o balanço, a interface e o contrato com o futuro
otimizador. Essa camada começa desativada e nunca é apresentada como modelo real.

## Interface

- **Visão geral** — KPIs, balanço, participação energética, três curvas FV e
  estado de maturidade dos subsistemas;
- **Entrada comum** — módulo, arranjo, perdas, CSV ou perfil sintético e janela
  de 120 minutos;
- **Modelos** — diagnóstico individual dos três estimadores solares, PEMFC/H₂ e
  bateria sintética;
- **Comparação solar** — potência, energia, eficiência, referência selecionável
  e diferenças relativas;
- **Exportação** — CSV configurável do EMS, de qualquer estimador FV, da PEMFC
  ou da bateria;
- **Otimizador** — contrato preparado para a integração do despacho ótimo;
- **Configurações** — diagnóstico de maturidade e hipóteses operacionais.

Todos os gráficos mantêm exportação SVG pelo menu Plotly.

## Contrato da entrada comum

O parser aceita CSV com vírgula ou ponto e vírgula, ponto ou vírgula decimal e
aliases usuais.

| Sinal canônico | Obrigatoriedade | Destino |
|---|---|---|
| `timestamp` | obrigatória | todos os blocos |
| `irradiancia_W_m2` | obrigatória | três estimadores FV |
| `temperatura_ambiente_C` | recomendada | NOCT, SDM e PEMFC |
| `potencia_solicitada_fc_kW` | opcional | PEMFC/H₂ |
| `carga_total_kW` | opcional | balanço e bateria |
| `FC_enable` | opcional | PEMFC |
| `T_coolant_in_C` | opcional | PEMFC |
| `V_bus_V` | opcional | PEMFC |

### Modo degradado

- Com GHI válida e temperatura ausente, o modelo de irradiância continua.
- NOCT, SDM e PEMFC são marcados como indisponíveis; não há preenchimento térmico silencioso.
- Se a camada sintética estiver ativa, uma referência PEMFC ausente pode ser criada
  explicitamente como sintética.
- GHI ausente ou uma janela temporal inválida bloqueiam a execução.

### Janela operacional

- 120 pontos;
- passo de 1 minuto;
- 2 horas de horizonte;
- fontes longas oferecem seleção por hora cheia;
- previsões fechadas de 120 pontos preservam o instante real, inclusive inícios
  como `12:01`.

O perfil padrão continua em `data/entrada_padrao_ems.csv`. Os exemplos originais
do motor solar estão em `data/exemplos_solar/`, inclusive o caso sem temperatura.

## Padrões do sistema

- módulo: Canadian Solar `CS7L-580MS`;
- arranjo: `2 módulos em série × 3 strings em paralelo`;
- total: 6 módulos;
- potência instalada: 3,480 kWp;
- perdas ópticas: 0 %;
- integração PEMFC na interface: 60 s.

## Executar localmente

Requer Python 3.12. O repositório inclui tanto `runtime.txt` quanto
`.python-version` para impedir que o deploy selecione Python 3.14 por padrão.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes verificam o contrato comum, janelas de 120 minutos, início em `HH:01`,
perfil sintético de 24 h, execução paralela dos três estimadores FV, exportação,
PEMFC, bateria sintética, balanço elétrico e modo degradado.

## Estrutura principal

```text
app.py
ems_app/
  charts.py
  data_pipeline.py
  model_runner.py
  multimodel_charts.py
  pages.py
  style.py
ems_core/
  solar/
    simulation/multimodel.py
  pemfc/
data/
assets/
docs/
tests/
```

Consulte `docs/MODELO_SOLAR_MULTIMODELO.md` para a formulação FV e os documentos
`MODEL_CARD_HORIZON_APPROX.md` e `METODOLOGIA_MODELO_HORIZON_APROX.md` para as
hipóteses da PEMFC.
