# ADR 0001 — Ambiente inicial e dependências

**Atualização S16:** A auditoria S16 encontrou/executou MATLAB R2024b Update9 instalado fora do PATH, verificou uma venv limpa offline e ambos os entrypoints. Versão do port0.1.0rc1. GUI Helvetica/fallback; plots Arial. Os dados de indisponibilidade/0.0.0 abaixo são a baseline histórica S0. Windows/Linux foram adiados pelo usuário, sem certificação.

Estado: adotado para preparação da Sprint 0, em 13/11/2026. Não anuncia suporte multiplataforma da aplicação.

O diretório inicial continha somente PRD, inventário, distribuição MATLAB e `.venv`. Não havia pacote Python, testes, metadados de instalação ou repositório Git inicializado na raiz. A arquitetura e a stack do PRD prevalecem; não há implementação Python anterior a preservar.

## Máquina e procedimento de comparação

| Item | Baseline |
| --- | --- |
| Modelo | Mac17,3, Apple M5, arm64 |
| CPU / memória | 10 CPUs lógicas; 17.179.869.184 bytes (16 GiB) |
| Sistema | macOS 27.2.1, build 26B131 |
| Interpretador | CPython 3.13.18, `.venv` na raiz |
| Qt / estilo previsto | Qt 6.12.0, Fusion claro e QSS próprio na Sprint 2 |
| Fonte de comparação | Arial; instalada em Qt e Matplotlib, sem redistribuição da fonte |
| Alvo principal de captura | Área cliente de 1366×768 pixels lógicos, escala 100%, DPR 1 |
| Outras escalas a verificar | 125%, 150%, 200%; registrar separadamente |
| Tela efetiva do smoke test | Plataforma Qt offscreen, tela virtual 800×800, 96 dpi, DPR 1 |
| Tela física / escala nativa | Não expostas nesta sessão; não inferidas da tela offscreen |
| MATLAB / Octave | Executáveis não encontrados no PATH; execução original indisponível |

O alvo de 1366×768 é uma **definição do protocolo**, não uma medição da tela física ou uma captura MATLAB já realizada. Antes de comparar pixels, capturar no desktop de referência, registrar ScreenSize, ScreenPixelsPerInch, posição interna da janela, escala do SO e DPR, e conferir a área cliente. Não comparar uma imagem offscreen com uma captura Retina sem converter explicitamente para pixels lógicos. A calibração final de decoração/insets depende dessa captura.

O hardware foi consultado com `sysctl`; SO com `sw_vers`. [environment.json](../../tests/reference/environment.json) registra importações, versões, fonte e propriedades efetivas do smoke test. Não se mediu desempenho científico nesta sprint: não há análise implementada. A partir de cada implementação, medir tempo com `perf_counter` e pico de RSS em processo isolado, sempre registrando dataset, tamanho, parâmetros, versão e unidades do RSS; não confundir RSS com apenas alocações Python.

## Resolução e congelamento

As versões foram resolvidas pelo pip 26.3 no PyPI e instaladas com wheels aceitos por CPython 3.13.18 neste Mac. Não são declaradas como “últimas”. Os sete pacotes diretos e suas dependências transitivas estão fixados em [requirements.txt](../../requirements.txt); pytest, pytest-qt, pypdf e setuptools e seus transitivos exclusivos estão em [requirements-dev.txt](../../requirements-dev.txt). PySide6 é o metapacote prescrito; seus componentes transitivos, inclusive Pdf/WebEngine, estão congelados, embora a aplicação use Qt Widgets. pypdf serve só à preparação das referências.

O relatório [dependency_resolution.json](../../tests/reference/dependency_resolution.json) preserva URLs públicas dos wheels e SHA-256 obtidos pelo pip; não contém credenciais. `pip check`, criação de canvas Agg/QtAgg, importação científica e teste Qt verificam compatibilidade inicial. Esses checks não validam algoritmos FracPaQ nem a aparência final.

Não atualizar pins durante a auditoria. Uma atualização intencional deve ser resolvida em ambiente separado, gerar relatórios pip --report, passar por `scripts/freeze_dependencies.py --pip-report ...` e repetir a validação científica/visual aplicável. Esse script altera os locks; não integra a verificação cotidiana. Wheels para Windows/Linux e outros patches Python ainda precisam ser testados; não anunciar compatibilidade só por metadados. Dependências condicionais de outro SO também devem ser congeladas quando esse SO for validado.

O pacote tem versão inicial `0.0.0`; FracPaQ 2.8 é a versão **de referência**, não a versão de entrega do port. Só existe `__init__.py` com metadados: entrypoints e GUI pertencem às próximas sprints, sem módulos vazios criados para simular implementação.
