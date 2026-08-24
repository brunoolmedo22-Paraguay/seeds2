# Origem dos núcleos de cálculo

Esta aplicação foi montada a partir das versões fornecidas pelo usuário em agosto de 2026:

- `solarsdm_ultima_version.zip`;
- `FC-PEM-66-KW-main.zip`.
- `Motor_solar_boat_h2-main`, incorporado ao SEED2 em 24/08/2026.

Os arquivos científicos foram organizados sob namespaces separados:

- `ems_core.solar`;
- `ems_core.pemfc`.

O motor multimodelo solar foi movido para `ems_core.solar.simulation.multimodel` e
seus gráficos para `ems_app.multimodel_charts`. A camada `ems_app.model_runner`
mantém uma única entrada, executa os três estimadores FV e conecta sua saída aos
demais subsistemas sem alterar a formulação científica original.
