# TODO

## Pendentes
- [ ] Rodar `python main.py --migrate-cache` para popular steam.genres/categories no cache local (operação ~15-30 min, requer STEAM_API_KEY). Sem isso, --list-tags e --show-tags não mostram dados.
- [ ] Após migrate-cache: FEZ será re-buscado na próxima execução (cache invalidado, threshold corrigido para 0.6).

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
- [x] --migrate-cache: popula steam.genres/categories para entradas legacy
