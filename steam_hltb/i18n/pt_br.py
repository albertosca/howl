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
    "setup.legacy_found": "\n  Encontrei um .env legado em {path}",
    "setup.legacy_now_reads": "  De agora em diante o howl lê de {path}.",
    "setup.legacy_migrated": "  Migrado para {path}",
    "setup.legacy_remove_hint": "  Pode remover o antigo quando quiser: rm {path}",
    "setup.header": "\n=== configuração do howl ===\n",
    "setup.igdb_intro": "\n  IGDB (opcional — notas para jogos removidos ou sem Metacritic):",
    "setup.igdb_step1": "  1. Acesse https://dev.twitch.tv/console e crie um app",
    "setup.igdb_step2": "  2. Categoria: Website Integration, OAuth Redirect URL: http://localhost",
    "setup.igdb_step3": "  3. Copie o Client ID e gere um Client Secret",
    "setup.summary": "\n--- Resumo ---",
    "setup.saved": "\n  Salvo em {path}",
    "setup.complete": "\nConfiguração concluída! Rode 'howl' para começar.\n",
    "setup.already_has": "\n  {path} já tem valores para: {keys}",
    "setup.cancelled": "\n\n  Configuração cancelada.",
    "setup.unexpected_error": "\n  Erro inesperado durante a configuração: {error}",
    "setup.error_logged": "  Detalhes registrados em {path}",
    "setup.keeping_existing": "  Mantendo os valores existentes.",
    "setup.prompt_igdb_id": "  IGDB Client ID: ",
    "setup.prompt_igdb_secret": "  IGDB Client Secret: ",
    "setup.prompt_migrate": "  Migrar agora? [S/n] ",
    "setup.prompt_igdb_now": "  Configurar o IGDB agora? [s/N] ",
    "setup.prompt_overwrite": "  Sobrescrever esses valores? [s/N] ",
    "setup.api_key_title": "\n  STEAM_API_KEY:",
    "setup.api_key_step1": "  1. Acesse https://steamcommunity.com/dev/apikey",
    "setup.api_key_step2": "  2. Entre com sua conta Steam",
    "setup.api_key_step3": "  3. Preencha 'Domain Name' com qualquer valor (ex: localhost)",
    "setup.api_key_step4": "  4. Copie a chave gerada",
    "setup.username_title": "\n  STEAM_USERNAME:",
    "setup.username_explain": "  É a vanity URL do seu perfil Steam.",
    "setup.username_example": (
        "  ex: steamcommunity.com/id/gabelogannewell → o username é gabelogannewell"
    ),
    "setup.vdf_title": "\n  STEAM_VDF_PATH (opcional — necessário para filtros de coleção):",
    "setup.vdf_none_found": "  Nenhum VDF detectado automaticamente.",
    "setup.api_key_present": "  STEAM_API_KEY já definida (***{suffix})",
    "setup.validating": "  Validando...",
    "setup.key_invalid": "inválida ou sem internet.",
    "setup.username_present": "\n  STEAM_USERNAME já definido: {username}",
    "setup.username_not_found": "não encontrado.",
    "setup.vdf_present": "\n  STEAM_VDF_PATH já definido: {path}",
    "setup.vdf_found": "  Encontrei {count} arquivo(s) VDF:",
    "setup.debug_valve": "\n  [debug] GET ResolveVanityURL (valve) → HTTP {status}",
    "setup.debug_resolve": "\n  [debug] GET ResolveVanityURL ({host}) → HTTP {status}",
    "setup.key_required": "  A chave é obrigatória.",
    "setup.key_unvalidated": "  Seguindo com a chave informada (não validada).",
    "setup.username_required": "  O username é obrigatório.",
    "setup.username_ok": "OK (SteamID: {steamid})",
    "setup.username_unvalidated": "  Seguindo com o username informado (não validado).",
    "setup.prompt_vdf_manual": "  Cole o caminho manualmente (ou Enter para pular): ",
    "setup.debug_key_neterr": "\n  [debug] erro de rede ao validar a chave: {error}",
    "setup.debug_user_neterr": "\n  [debug] erro de rede ao validar o username: {error}",
    "setup.prompt_key": "\n  Cole sua chave: ",
    "setup.prompt_username": "\n  Seu username: ",
    "setup.prompt_vdf_choice": "  Escolha [1-{max}] ou Enter para pular: ",
    "setup.prompt_use_existing": "  Usar o existente? [S/n] ",
    "setup.prompt_retry": "  Tentar de novo? [S/n] ",
    "setup.answer_no": "não",
    "setup.answer_yes": "sim",
    "tui.filters_title": "── Filtros ──────────────",
    "tui.label_name": "Nome (fuzzy)",
    "tui.label_sort": "Ordem",
    "tui.label_top": "Top N",
    "tui.label_genres": "Gêneros (por vírgula)",
    "tui.label_exclude": "Excluir gêneros",
    "tui.label_progress": "Progresso",
    "tui.label_category": "Categoria",
    "tui.label_min_hours": "Horas mín.",
    "tui.label_max_hours": "Horas máx.",
    "tui.label_collection": "Coleção",
    "tui.label_era": "Era de lançamento",
    "tui.saved": "Salvo em output/howl.csv e .md",
    "tui.status_bar": " Mostrando {shown} de {total} filtrados · ordem: {sort}",
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
