_EPILOG = """
Exemplos:
  howl --username meusteamid --top 25 --sort rated
  howl --username meusteamid --genre "action,rpg" --not-started --top 10
  howl --username meusteamid --tui --sort shortest
  howl --username meusteamid --era "2010-2015,2015-2020" --sort quick-wins

  Dica: defina STEAM_USERNAME no seu ambiente para não passar --username toda vez.

Formatos de entrada:
  --genre / --genre-any / --exclude-genre  nomes separados por vírgula (ex: "action,rpg")
  --sort      shortest | longest | rated | loved | quick-wins | hidden-gems | composto
  --era       separadas por vírgula: pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown
  --weight-mc / --weight-steam             pesos 0.0-1.0 que somam 1.0 (ex: 0.6 e 0.4)
"""

MESSAGES: dict[str, str] = {
    "test.plain": "português puro",
    "test.interpolated": "{count} itens",
    "report.header": " TOP {top} — ordem: {sort}  ({shown} de {total} filtrados)",
    "report.too_few": " ⚠  Apenas {total} jogos passaram nos filtros (pedido: {top})",
    "report.col_name": "Nome",
    "report.col_year": "Ano",
    "report.col_played": "Jogado",
    "report.col_score": "Nota",
    "report.no_collections": "Nenhuma coleção encontrada. Confira --vdf-path.",
    "report.available_collections": " Coleções disponíveis ({count} únicas)",
    "report.no_items": "Nenhum {field} no cache. Tente --refresh ou --migrate-cache.",
    "report.available_items": " {field} disponíveis ({count} únicos)",
    "report.saved": "\nSalvo em '{csv}' e '{md}'",
    "report.interactive_header": "\n=== Modo Interativo ===\n",
    "migrate.slow_warning": (
        "⚠  Isso pode demorar 15-30 min. Ctrl+C para interromper (progresso salvo)."
    ),
    "migrate.done": "Migração concluída.",
    "migrate.igdb_done": "Migração IGDB concluída.",
    "args.description": (
        "HOWL — Hoard Optimizer, What to Launch. Ranqueia sua biblioteca Steam por "
        "qualidade × tempo investido."
    ),
    "args.lang": "Idioma da interface (padrão: do setup, do ambiente ou do locale do sistema)",
    "args.epilog": _EPILOG,
    "args.username": "Vanity URL do perfil Steam (ou variável STEAM_USERNAME)",
    "args.sort": "Critério de ordenação (padrão: %(default)s)",
    "args.genre": "Gêneros obrigatórios, separados por vírgula (ex: 'action,rpg')",
    "args.genre_any": "Ao menos um destes gêneros (separados por vírgula)",
    "args.exclude_genre": "Gêneros a excluir (separados por vírgula)",
    "args.not_started": "Apenas jogos nunca jogados (0h)",
    "args.in_progress": "Apenas jogos começados mas não terminados",
    "args.all_progress": "Sem filtro de progresso (inclui jogos terminados)",
    "args.category": "Filtra por tipo de jogo (padrão: %(default)s)",
    "args.min_hours": "Duração mínima no HLTB, em horas",
    "args.max_hours": "Duração máxima no HLTB, em horas",
    "args.era": (
        "Eras de lançamento (separadas por vírgula): pre-2005, 2005-2010, 2010-2015, "
        "2015-2020, 2020+, unknown"
    ),
    "args.top": "Quantos jogos mostrar (padrão: %(default)s)",
    "args.output": "Nome-base dos arquivos .csv e .md de saída (padrão: %(default)s)",
    "args.weight_mc": "Peso do Metacritic na nota composta (padrão: %(default)s)",
    "args.weight_steam": "Peso das reviews da Steam na nota composta (padrão: %(default)s)",
    "args.collection": "Filtra pelo nome de uma coleção da Steam (ex: 'Playing', 'Multiplayer')",
    "args.vdf_path": (
        "Caminho do sharedconfig.vdf da Steam (padrão: variável STEAM_VDF_PATH ou sharedconfig.vdf)"
    ),
    "args.show_finished": "Inclui jogos da coleção 'Finished' (excluídos por padrão)",
    "args.list_tags": "Lista todas as categorias Steam disponíveis no cache e sai",
    "args.list_genres": "Lista todos os gêneros disponíveis no cache e sai",
    "args.list_collections": "Lista as coleções Steam disponíveis no VDF e sai",
    "args.refresh": "Busca jogos novos da biblioteca Steam (igual ao comportamento padrão)",
    "args.refresh_all": "Rebusca os dados de todos os jogos, inclusive os já em cache (lento)",
    "args.migrate_cache": (
        "Preenche steam.genres/categories/release_year nas entradas incompletas do "
        "cache (~15-30 min)"
    ),
    "args.migrate_igdb": (
        "Busca dados do IGDB para jogos sem Metacritic no cache (exige IGDB_CLIENT_ID "
        "e IGDB_CLIENT_SECRET)"
    ),
    "args.verbose": "Mostra progresso detalhado de todos os jogos (inclusive os em cache)",
    "args.show_tags": "Mostra as categorias Steam na tabela (além dos gêneros)",
    "args.interactive": "Modo interativo por perguntas",
    "args.tui": "Abre a interface visual interativa (estilo htop)",
    "args.setup": "Configura as variáveis de ambiente interativamente",
}

# Keyed by argparse's own English source strings, which is what the gettext
# alias receives. See argparse_hook.CORE_STRINGS for the supported set.
ARGPARSE: dict[str, str] = {
    " (default: %(default)s)": " (padrão: %(default)s)",
    "%(heading)s:": "%(heading)s:",
    "%(prog)s: error: %(message)s\n": "%(prog)s: erro: %(message)s\n",
    "ambiguous option: %(option)s could match %(matches)s": (
        "opção ambígua: %(option)s pode corresponder a %(matches)s"
    ),
    'argument "-" with mode %r': 'argumento "-" com modo %r',
    "argument %(argument_name)s: %(message)s": "argumento %(argument_name)s: %(message)s",
    "can't open '%(filename)s': %(error)s": "não foi possível abrir '%(filename)s': %(error)s",
    "conflicting option string: %s": "opção conflitante: %s",
    "conflicting option strings: %s": "opções conflitantes: %s",
    "expected %s argument": "esperava %s argumento",
    "expected %s arguments": "esperava %s argumentos",
    "expected at least one argument": "esperava ao menos um argumento",
    "expected at most one argument": "esperava no máximo um argumento",
    "expected one argument": "esperava um argumento",
    "ignored explicit argument %r": "argumento explícito ignorado: %r",
    "invalid %(type)s value: %(value)r": "valor %(type)s inválido: %(value)r",
    "invalid choice: %(value)r (choose from %(choices)s)": (
        "escolha inválida: %(value)r (opções: %(choices)s)"
    ),
    "not allowed with argument %s": "não permitido junto com o argumento %s",
    "one of the arguments %s is required": "um dos argumentos %s é obrigatório",
    "options": "opções",
    "positional arguments": "argumentos posicionais",
    "show program's version number and exit": "mostra a versão do programa e sai",
    "show this help message and exit": "mostra esta ajuda e sai",
    "the following arguments are required: %s": "os seguintes argumentos são obrigatórios: %s",
    "unexpected option string: %s": "opção inesperada: %s",
    "unknown parser %(parser_name)r (choices: %(choices)s)": (
        "parser desconhecido %(parser_name)r (opções: %(choices)s)"
    ),
    "unrecognized arguments: %s": "argumentos não reconhecidos: %s",
    "usage: ": "uso: ",
}
