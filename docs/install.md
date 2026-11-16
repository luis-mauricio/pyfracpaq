# Instalação e entrega local

O candidato0.1.0rc1 foi verificado em CPython3.13.18/macOS arm64. A aplicação funciona offline depois da instalação. Windows/Linux ficam para teste posterior pelo usuário, conforme instrução de14/11/2026. As diferenças científicas autorizadas e a homologação visual ainda aberta estão no [relatório S16](parity/sprint-16.md).

## Código e ambiente de desenvolvimento

Na raiz do projeto, escolher explicitamente Python3.13; o `python3` do sistema pode ser3.9 ou3.14. Não reutilizar uma venv de outro minor.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install -e . --no-deps --no-build-isolation
.venv/bin/python -m pip check
.venv/bin/python run_gui.py
# alternativa, também fora da raiz depois de instalado:
.venv/bin/python -m pyfracpaq
```

No VS Code, abrir a pasta do projeto e selecionar `.venv/bin/python`. O workspace inclui as duas configurações de execução em `.vscode/launch.json`. O botão Run Python File funciona com run_gui.py. Se houver uma seleção antiga apontando ao diretório `.venv`, selecionar novamente o executável, pois esse diretório não é um comando Python. As configurações entregues são para o Mac verificado; no Windows será necessário selecionar `.venv\Scripts\python.exe`.

## Instalar sem rede

Ao extrair o ZIP de fontes, transportar também o wheel e o wheelhouse para `dist/` da cópia extraída; eles são artefatos separados.

`dist/` contém o wheel do port e `wheelhouse-macos-arm64/` com os wheels fixados de execução/desenvolvimento. Não se exige MATLAB para executar o port. Arial/Helvetica usam a instalação local do sistema; as fontes não são redistribuídas.

```bash
python3.13 -m venv /tmp/pyfracpaq-local/.venv
/tmp/pyfracpaq-local/.venv/bin/python -m pip install \
  --no-index --find-links dist/wheelhouse-macos-arm64 \
  dist/pyfracpaq-0.1.0rc1-py3-none-any.whl
/tmp/pyfracpaq-local/.venv/bin/python -m pip check
/tmp/pyfracpaq-local/.venv/bin/python -m pyfracpaq
```

Para desenvolvimento offline, usar a mesma opção `--no-index --find-links` com `-r requirements-dev.txt`. O wheelhouse contém wheels macOS arm64/CPython3.13 e dependências universais; não o anunciar como instalação Windows/Linux. `SHA256SUMS` permite conferir os arquivos antes de transportar a entrega. Obter dependências em outro ambiente exigirá preparar um wheelhouse compatível; não mudar os pins silenciosamente.

## Verificar a entrega

```bash
.venv/bin/python scripts/check_local_delivery.py \
  --python /tmp/pyfracpaq-local/.venv/bin/python \
  --output /tmp/pyfracpaq-local-check.json
.venv/bin/python scripts/run_isolated_tests.py \
  --report /tmp/pyfracpaq-tests.json
```

O primeiro comando executa TXT/SVG/Hough e os dois entrypoints do pacote instalado, fora da raiz, bloqueando connect/DNS. Qt offscreen não certifica aparência nativa. O segundo copia o projeto para uma pasta temporária e inclui exatamente os164 arquivos originais do manifesto. Não remove nem modifica resultados existentes junto aos fontes MATLAB. O verificador original continua estrito: executar source_manifest.py diretamente numa pasta com arquivos extras deve acusá-los. A pasta original já fornecida deve permanecer disponível para os testes; o wheel isolado de execução não inclui essa distribuição nem os testes.

Os relatórios registram a pasta isolada, saída/retorno e JUnit. Resultados de exemplo do usuário na raiz nunca são incluídos como fontes nem substituídos pelos testes. A exportação normal da GUI continua usando o diretório corrente; escolher pasta/tag para cada trabalho e conferir as mensagens Saved/Replaced.
