# Sprint15 — Utilitários, bibliotecas e legado

Sprint concluída. [Todos19 AUX e164 arquivos têm destinação](legacy.md), com [contratos](../decisions/0017-complementary-tools-and-legacy.md), [manual local](../user-guide.md), [exemplos válidos](../../examples/README.md), [comparações nativas](../../tests/reference/sprint15/native_comparison.json) e [figuras de apoio](../../tests/reference/sprint15/validation.json).

Ferramentas locais: preparo RGB/grayscale com TIFF/painel6etapas, Move com cabeçalho/colunas/EOF explícitos e diálogo wavelet separado com14objetos/defaults, Run/Cancel seguro e reutilização do raster. APIs complementares: readtext genérico, tensor16, rosas linear/histórica, probePlane, pivô/aplicação de paletas e desenho auxiliar. Geometria, RGB,18paletas e variograma avançado existentes foram preservados/reutilizados, sem repetir tarefas já concluídas.

As seis etapas de preparo coincidem exatamente com o script MATLAB no caso registrado. Tensor16, projeção, probePlane, paleta com pivô, readtext e dados de rosas têm comparação com arrays reais. Declaram-se as limitações históricas de probePlane e do parser pivot MATLAB, sem correção científica silenciosa. [Procedência nativa](../../tests/reference/sprint15/native_provenance.json).

Interface2.2 semFIG, assinaturas antigas, variantes wavelet e experimentos incompletos de rosas/cores permanecem referência. Arquivos da página histórica e metadados params.json ficam preservados, sem hospedagem/configuração da GUI. Formatos de scripts antigos têm destinação explícita; sessão/relatório continuam extensões futuras. Créditos e avisos preservam autores originais e distinguem reimplementação matemática de cópia de código. [Checagens finais](../../tests/reference/sprint15/checks.json).
