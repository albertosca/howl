MESSAGES: dict[str, str] = {
    "test.plain": "português puro",
    "test.interpolated": "{count} itens",
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
