# Organização do repositório — 16/11/2026

O usuário aprovou mover os resultados soltos na raiz e os dois documentos de planejamento. As demais mudanças de estrutura dependem de consulta antes da execução.

| Origem | Destino | Tratamento |
| --- | --- | --- |
| 8 PNGs e 6 TXTs `FracPaQ2D…` na raiz | `outputs/previous-runs/` | Conteúdo preservado byte a byte; continuam ignorados pelo Git. |
| `PRD.md` | [docs/planning/PRD.md](../planning/PRD.md) | Links relativos ajustados; aprovação dos documentos registrada. |
| `FUNCIONALIDADES_FRACPAQ.md` | [docs/planning/FUNCIONALIDADES_FRACPAQ.md](../planning/FUNCIONALIDADES_FRACPAQ.md) | Links relativos ajustados. |

O índice de paridade passa a ler os documentos em docs/planning. O roteiro de snapshot completo os encontra pela árvore docs. A regra export-ignore continua excluindo o planejamento do ZIP de uso. O diretório de saída usado pelo aplicativo continua sendo o diretório corrente; esta organização preserva o contrato de execução documentado.

README e manuais pt-BR/inglês foram aprovados explicitamente pelo usuário e permanecem com os mesmos hashes. Nenhum algoritmo, recurso, exemplo ou referência científica foi movido ou alterado. Os relatórios antigos mantêm os caminhos/hashes de sua época. A referência a prd-bruto.md já não tinha arquivo de destino antes da mudança; ela continua sendo uma referência histórica do PRD, sem inventar um arquivo substituto.

## Revisão das demais pastas

- `pyfracpaq/`: separação existente por domínio, geometria, entrada/saída, análise, gráficos, interface, workers, recursos e ferramentas adequada; manter.
- `examples/`: oito arquivos, incluindo índice e procedência; manter junto para preservar os exemplos aprovados nos manuais.
- `docs/manual/`: capítulos separados por idioma, estilo e 52 imagens compartilhados; manter.
- `docs/decisions/`, `docs/parity/`, `docs/releases/`, `docs/licenses/`: conteúdo já separado por finalidade; manter.
- `tests/`: separado em numerical, gui, visual, fixtures e reference. Referências organizadas por sprint/assunto e ligadas a evidências aceitas; preservar seus caminhos.
- `scripts/`: 71 arquivos diretamente na pasta, Python e MATLAB. Há oportunidade de agrupamento por finalidade, com revisão dos imports/comandos; proposta ainda não executada.
- `dist/`, `build/`, ambiente virtual, metadados egg-info e caches: locais/ignorados; preservados. Arquivos históricos não foram apagados nem movidos nesta etapa.
- `fracpaq-matlab/`: referência local ignorada, com integridade científica preservada; manter.

As verificações e hashes estão em [repository-organisation.json](../../tests/reference/sprint16/delivery/point-5/repository-organisation.json). A S16-09.5 permanece aberta para envio do usuário ao GitHub e conferência remota; não houve commit/push/publicação.

## Verificação concluída

Foram conferidos 358 links locais, os 164 IDs do inventário e todos os caminhos do snapshot completo. Os 14 resultados mantêm seus hashes e estão ignorados no novo destino. O candidato ZIP de uso foi atualizado: 262 arquivos, aproximadamente 46,68 MiB, sem planejamento, resultados locais, testes ou ferramentas internas; README, PDFs e fontes LaTeX permanecem idênticos aos aprovados.

As 14 verificações direcionadas de caminhos/contratos passaram. A primeira execução incluiu também um teste antigo de distribuição estrita, que rejeita oito arquivos adicionais já conhecidos na referência MATLAB; esse teste falhou. A auditoria atual confirmou por SHA-256 os 164 originais e os oito arquivos adicionais registrados na Sprint 11, todos intactos. A falha está registrada separadamente e não foi convertida em aprovação nem corrigida apagando/modificando a referência local.
