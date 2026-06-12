# TODO

## Em andamento
- [ ] Reconstruir cache com `howl --verbose` (cache atual tem só 1 jogo após sobrescrita de teste). Todos os jogos novos já saem com genres + release_year automaticamente — sem necessidade de --migrate-cache.

## Pendentes
- [ ] FEZ será re-buscado na próxima execução (cache invalidado, threshold corrigido para 0.6).

## Próxima tarefa grande: Tornar o projeto público e agnóstico

Objetivo: qualquer pessoa consegue clonar, instalar e rodar sem depender de dados pessoais do Alberto.

- [ ] **Dados pessoais:** remover username "heenett" hardcoded do código; varrer histórico de commits por outros dados pessoais; garantir que nada sensível vai parar no repo
- [ ] **Configuração:** `--username` obrigatório (sem default pessoal); deixar claro o que é obrigatório vs opcional em cada flag e no README
- [ ] **.gitignore:** revisar e caprichar — `games_cache.json`, `sharedconfig.vdf`, `.env`, outputs CSV/MD, `__pycache__`, `venv/`, `*.egg-info`
- [ ] **Instruções de setup:** passo a passo para obter STEAM_API_KEY (link direto, print do que clicar), onde achar o `sharedconfig.vdf` em cada OS (Windows/Mac/Linux), o que acontece se não tiver Metacritic (fallback)
- [ ] **Requisitos mínimos:** Python 3.11+, Steam account público (ou API key própria), ~500MB RAM para TUI, nota de que HLTB throttling significa ~5 min por 300 jogos
- [ ] **Documentação 10/10:** README completo; exemplos reais de output; seção de troubleshooting; badges (testes passando, versão Python)
- [ ] **Code review master blaster:** zero magic strings sem constante, type hints em tudo, docstrings onde o WHY não é óbvio, sem dead code, nomes de variável sem abreviação desnecessária, mypy/ruff clean

## Resolvidos
- [x] .gitignore (games_cache.json, venv/, outputs, sharedconfig.vdf)
- [x] Print clutter: fetch.py silencioso por padrão, verbose só com --verbose
- [x] interactive.py: RAWG removido, build_library corrigido, collection adicionado
- [x] --list-collections: lista coleções do VDF com contagem
- [x] Top-N warning: aviso quando menos jogos que --top passam nos filtros
- [x] FEZTAL: threshold 0.5 → 0.6 (entrada FEZ invalidada no cache)
- [x] Tags RAWG descartadas: --show-tags e TUI usam apenas steam.categories (gameplay, sem noise)
- [x] TUI: Select de coleção (todas / Jogando / Multiplayer)
- [x] Terminados excluídos de todas as views por padrão (--show-finished para override)
- [x] --migrate-cache: popula steam.genres/categories/release_year para entradas incompletas
- [x] Reestruturação em pacote Python (steam_hltb/), pyproject.toml, CLI howl
- [x] TUI: era checkboxes, coluna Ano, fuzzy filter por nome
- [x] 7 fórmulas de sort: shortest, longest, rated, loved, quick-wins, hidden-gems, composto
- [x] 147 testes cobrindo todos os módulos
- [x] Renomear CLI para howl (HOWL — Hoard Optimizer, What to Launch)
- [x] README.md inicial
