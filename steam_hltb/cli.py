import argparse
import os
import sys

from .score import SORT_OPTIONS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="howl",
        description=(
            "HOWL — Hoard Optimizer, What to Launch. "
            "Ranqueia sua biblioteca Steam por qualidade × tempo."
        ),
        epilog="""
Exemplos:
  howl --username mysteamid --top 25 --sort rated
  howl --username mysteamid --genre "action,rpg" --not-started --top 10
  howl --username mysteamid --tui --sort shortest
  howl --username mysteamid --era "2010-2015,2015-2020" --sort quick-wins

  Dica: defina STEAM_USERNAME no ambiente para não precisar de --username.

Formatos de entrada:
  --genre / --genre-any / --exclude-genre  nomes vírgula-sep (ex: "action,rpg")
  --sort      shortest | longest | rated | loved | quick-wins | hidden-gems | composto
  --era       vírgula-sep: pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown
  --weight-mc / --weight-steam             pesos 0.0-1.0 que somam 1.0 (ex: 0.6 e 0.4)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--username",
        default=os.environ.get("STEAM_USERNAME"),
        help="Vanity URL do perfil Steam (ou env STEAM_USERNAME)",
    )
    p.add_argument(
        "--sort",
        default="shortest",
        choices=SORT_OPTIONS,
        help="Critério de ordenação (padrão: %(default)s)",
    )
    p.add_argument("--genre", help="Gêneros obrigatórios, separados por vírgula (ex: 'action,rpg')")
    p.add_argument("--genre-any", help="Pelo menos um desses gêneros (separados por vírgula)")
    p.add_argument("--exclude-genre", help="Gêneros a excluir (separados por vírgula)")

    prog = p.add_mutually_exclusive_group()
    prog.add_argument("--not-started", action="store_true", help="Somente jogos nunca jogados (0h)")
    prog.add_argument(
        "--in-progress", action="store_true", help="Somente jogos iniciados e não zerados"
    )
    prog.add_argument(
        "--all-progress",
        action="store_true",
        help="Sem filtro de progresso (inclui jogos já zerados)",
    )

    p.add_argument(
        "--category",
        default="all",
        choices=["all", "singleplayer", "coop"],
        help="Filtrar por tipo de jogo (padrão: %(default)s)",
    )
    p.add_argument("--min-hours", type=float, help="Duração mínima HLTB em horas")
    p.add_argument("--max-hours", type=float, help="Duração máxima HLTB em horas")
    p.add_argument(
        "--era",
        help=(
            "Épocas de lançamento (vírgula-sep): "
            "pre-2005, 2005-2010, 2010-2015, 2015-2020, 2020+, unknown"
        ),
    )
    p.add_argument("--top", type=int, default=10, help="Quantos jogos exibir (padrão: %(default)s)")
    p.add_argument(
        "--output",
        default="howl_output",
        help="Nome base dos arquivos de saída .csv e .md (padrão: %(default)s)",
    )
    p.add_argument(
        "--weight-mc",
        type=float,
        default=0.5,
        help="Peso do Metacritic no score composto (padrão: %(default)s)",
    )
    p.add_argument(
        "--weight-steam",
        type=float,
        default=0.5,
        help="Peso do Steam no score composto (padrão: %(default)s)",
    )
    p.add_argument("--collection", help="Filtrar por coleção Steam (ex: 'Jogando', 'Multiplayer')")
    p.add_argument(
        "--vdf-path",
        default=os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf"),
        help=(
            "Caminho para o sharedconfig.vdf do Steam "
            "(padrão: STEAM_VDF_PATH env ou sharedconfig.vdf)"
        ),
    )
    p.add_argument(
        "--show-finished",
        action="store_true",
        help="Incluir jogos da coleção 'Terminados' (excluídos por padrão)",
    )
    p.add_argument(
        "--list-tags",
        action="store_true",
        help="Lista todas as categorias disponíveis no cache e sai",
    )
    p.add_argument(
        "--list-genres",
        action="store_true",
        help="Lista todos os gêneros disponíveis no cache e sai",
    )
    p.add_argument(
        "--list-collections",
        action="store_true",
        help="Lista coleções Steam disponíveis no VDF e sai",
    )
    p.add_argument("--refresh", action="store_true", help="Ignora o cache e rebusca todos os jogos")
    p.add_argument(
        "--migrate-cache",
        action="store_true",
        help="Preenche steam.genres/categories/release_year para entradas incompletas (~15-30 min)",
    )
    p.add_argument(
        "--migrate-igdb",
        action="store_true",
        help=(
            "Busca dados IGDB para jogos sem Metacritic no cache "
            "(requer IGDB_CLIENT_ID e IGDB_CLIENT_SECRET)"
        ),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Exibe progresso detalhado de todos os jogos (inclusive cache)",
    )
    p.add_argument(
        "--show-tags",
        action="store_true",
        help="Exibe categorias Steam dos jogos na tabela (além de gêneros)",
    )
    p.add_argument("--interactive", action="store_true", help="Modo interativo via prompts")
    p.add_argument(
        "--tui", action="store_true", help="Abre interface visual interativa (htop-style)"
    )
    p.add_argument(
        "--setup", action="store_true", help="Configura variáveis de ambiente interativamente"
    )
    return p.parse_args()


def _resolve_username(args: argparse.Namespace) -> str:
    """Retorna username do argparse, env var, ou prompt interativo."""
    if args.username:
        username: str = args.username
        return username
    username = input("Steam username (vanity URL do perfil): ").strip()
    if not username:
        print("Erro: username obrigatório.", file=sys.stderr)
        sys.exit(1)
    return username


def _progress_mode(args: argparse.Namespace) -> str:
    if args.not_started:
        return "not_started"
    if args.in_progress:
        return "in_progress"
    if args.all_progress:
        return "all"
    return "default"


def _weights(args: argparse.Namespace) -> dict[str, float]:
    w: dict[str, float] = {"mc": args.weight_mc, "steam": args.weight_steam}
    total = sum(w.values())
    if abs(total - 1.0) > 0.01:
        print(f"Aviso: pesos somam {total:.2f}, esperado 1.0. Normalizando.", file=sys.stderr)
        w = {k: v / total for k, v in w.items()}
    return w


def _csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    result = [v.strip() for v in value.split(",") if v.strip()]
    return result or None
