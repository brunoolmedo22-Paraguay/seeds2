# Origem dos núcleos de cálculo

Esta aplicação foi montada a partir das versões fornecidas pelo usuário em 09/08/2026:

- `solarsdm_ultima_version.zip`;
- `FC-PEM-66-KW-main.zip`.

Os arquivos científicos foram organizados sob namespaces separados:

- `ems_core.solar`;
- `ems_core.pemfc`.

As alterações mecânicas feitas nesses núcleos se limitam aos caminhos de importação necessários para evitar colisões entre pacotes homônimos. A lógica de cálculo é consumida pela camada `ems_app.model_runner`.
