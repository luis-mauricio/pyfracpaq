# Preparação e execução pelo código

**Forma de distribuição definida pelo usuário em 16/11/2026:** código no GitHub, obtido por clone ou download ZIP. A aplicação roda na pasta do projeto, pelo terminal ou VS Code, com Python 3.13. Miniforge pode fornecer o ambiente Python. Não é necessário instalar o pacote PyFracPaQ e não haverá entrega de instaladores, wheels ou wheelhouse para usuários. A decisão técnica está em docs/decisions/0019-source-distribution.md no repositório completo.

Versão dos fontes: **0.9.0rc1**, November 2026, contato luismauricio@me.com. Referência MATLAB: FracPaQ 2.8. Testes e relatórios de desenvolvimento ficam no repositório completo e fora do ZIP de uso. Sua ausência não impede nenhuma análise.

## Python e ambiente virtual

Obter o repositório ou extrair o ZIP do GitHub e abrir a pasta que contém run_gui.py e requirements.txt. Com Python 3.13 instalado, executar nessa pasta:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python run_gui.py
# alternativa, na mesma pasta:
.venv/bin/python -m pyfracpaq
```

Os comandos acima são para o ambiente macOS verificado. Não executar pip install do projeto nem criar wheel para usar o programa. requirements.txt instala as dependências, mantendo os pins do projeto. A obtenção inicial do código/dependências pode exigir rede; a operação das análises é local/offline depois da preparação.

## VS Code e Miniforge

No VS Code, abrir a pasta do projeto, selecionar o executável Python do ambiente preparado e iniciar run_gui.py ou usar as configurações de .vscode/launch.json. O interpretador é o executável dentro do ambiente, não o diretório .venv. O VS Code utiliza esse Python para executar o código.

Com Miniforge, criar um ambiente com `conda create -n pyfracpaq python=3.13 pip`, ativar com `conda activate pyfracpaq`, abrir o terminal na raiz do projeto e executar:

```bash
python -m pip install -r requirements.txt
python -m pip check
python run_gui.py
# alternativa:
python -m pyfracpaq
```

No VS Code, selecionar o Python desse ambiente Miniforge. Não é preciso criar também uma .venv dentro de um ambiente já preparado. A validação documentada informa as versões e os cenários conferidos; não representa certificação de Windows/Linux.

Foram verificados CPython 3.13.18 em ambiente virtual e Python 3.13.13 em ambiente Miniforge, ambos no macOS arm64, com instalação somente de requirements.txt e execução diretamente pelo código. O código exige Python >=3.13,<3.14. Windows/Linux permanecem para os testes posteriores do usuário, conforme sua instrução. Não é necessário MATLAB para usar o programa.

## Desenvolvimento e referências

Para executar testes e ferramentas de comparação, instalar adicionalmente requirements-dev.txt. A instalação editável do projeto é opcional para desenvolvimento, sem ser requisito de uso. Os testes específicos de referências exigem a pasta fracpaq-matlab, mantida separadamente e fora do Git; ela não é necessária para executar a aplicação. Não confundir ausência dessa referência com ausência das funções do port.

A mesma tag substitui os mesmos arquivos; tags diferentes coexistem, exceto os intermediários de nome fixo. A substituição é atômica por arquivo, sem transação conjunta para todo o Run. Conversões SVG ficam junto ao SVG; demais saídas usam o diretório de execução. Preservar as entradas originais e conferir as mensagens Saved/Replaced.

Os pacotes 0.1.0rc1 e os artefatos 0.9.0rc1 em dist/ foram produzidos antes da definição de distribuição pelo GitHub. São evidências técnicas internas, não produtos para instalar ou distribuir. Seus testes de instalação não concluem o ponto 4 redefinido. Os relatórios dessa execução permanecem em docs/parity/ no repositório completo. [Notas para o usuário](release-notes.md).

## O que vem no ZIP de uso

Programa e recursos em pyfracpaq/, run_gui.py, requirements.txt, exemplos, configurações de execução do VS Code, manual, notas e licenças. Testes, evidências e scripts internos ficam fora desse ZIP por .gitattributes/export-ignore. O clone completo conserva esse material para manutenção, mas nada dele é necessário em tempo de execução. A descoberta automática de testes no VS Code fica desativada; desenvolvedores podem habilitá-la após preparar requirements-dev.txt.
