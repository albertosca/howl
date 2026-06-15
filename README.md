# HOWL

**Hoard Optimizer, What to Launch**

Ranqueia sua biblioteca Steam por qualidade × tempo investido usando dados do [HowLongToBeat](https://howlongtobeat.com), Metacritic e Steam Reviews. Chega de paralisia de decisão na frente da backlog.

```
  #  Nome                                            Ano    MC   Steam   HLTB   Jogadas     Score
---  ---------------------------------------------- ----  ----  ------  -----  --------  --------
  1  Hades                                          2020    93     97%    22h        0h      20.3
     ↳ action, roguelike
  2  Hollow Knight                                  2017    87     95%    40h        5h      14.4
     ↳ action, platformer
```

## Requisitos

- Python 3.11+
- Steam API Key (gratuita, instruções abaixo)
- Conta Steam com perfil e biblioteca públicos (ou privados com a própria chave)

## Instalação

```bash
git clone https://github.com/albertosca/howl.git
cd howl
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

Após instalar, o comando `howl` fica disponível no ambiente:

```bash
howl --help
```

## Configuração

### Jeito rápido: `howl --setup`

```bash
howl --setup
```

O wizard interativo guia você pelas variáveis necessárias, valida ao vivo contra a Steam API e escreve um `.env` local (carregado automaticamente) ou mostra o bloco pra colar no seu shell profile.

### Jeito manual: variáveis de ambiente

| Variável | Obrigatória | O que é |
|---|---|---|
| `STEAM_API_KEY` | sim | Chave da Steam Web API |
| `STEAM_USERNAME` | sim | Vanity URL do seu perfil (ex: `gabelogannewell`) |
| `STEAM_VDF_PATH` | não | Caminho para o `sharedconfig.vdf` (filtros de coleção) |
| `IGDB_CLIENT_ID` | não | Client ID do app Twitch (para scores de jogos delisted) |
| `IGDB_CLIENT_SECRET` | não | Client Secret do app Twitch |

**STEAM_API_KEY:**
1. Acesse https://steamcommunity.com/dev/apikey
2. Faça login com sua conta Steam
3. Preencha "Domain Name" com qualquer valor (ex: `localhost`)
4. Copie a chave gerada

**STEAM_USERNAME:**
A vanity URL do seu perfil Steam: `steamcommunity.com/id/gabelogannewell` → username é `gabelogannewell`

**IGDB_CLIENT_ID e IGDB_CLIENT_SECRET (opcional):**
O IGDB complementa o Metacritic para jogos que o Steam não retorna score (delisted, muito antigos, etc.).

1. Acesse https://dev.twitch.tv/console e faça login com sua conta Twitch (crie uma se não tiver — é grátis)
2. Clique em **Register Your Application**
3. Preencha:
   - **Name:** qualquer coisa (ex: `howl-igdb`)
   - **OAuth Redirect URLs:** `http://localhost`
   - **Category:** `Website Integration`
4. Clique em **Create**
5. Na lista de apps, clique em **Manage**
6. Copie o **Client ID**
7. Clique em **New Secret** e copie o **Client Secret** (aparece só uma vez)

Com as credenciais no `.env`, rode:
```bash
howl --migrate-igdb
```
O token OAuth é gerado e renovado automaticamente. Não é preciso refazer esse processo.

**STEAM_VDF_PATH (opcional):**
Necessário para usar `--collection` e exclusão automática de jogos terminados.

| Sistema | Localização padrão |
|---|---|
| macOS | `~/Library/Application Support/Steam/userdata/<steamid>/7/remote/sharedconfig.vdf` |
| Linux | `~/.steam/steam/userdata/<steamid>/7/remote/sharedconfig.vdf` |
| Windows | `C:\Program Files (x86)\Steam\userdata\<steamid>\7\remote\sharedconfig.vdf` |

O `<steamid>` é numérico (diferente da vanity URL). Encontre em: Steam → Configurações → Conta → ID da conta Steam.

Para definir as vars permanentemente (alternativa ao `.env`):

```bash
# Adicione ao ~/.zshenv ou ~/.zprofile
export STEAM_API_KEY="sua_chave_aqui"
export STEAM_USERNAME="seu_username"
export STEAM_VDF_PATH="/caminho/para/sharedconfig.vdf"  # opcional
```

## Uso

```bash
# Primeiro uso: popula o cache (pode demorar ~5 min para 300 jogos)
howl --username meu_id_steam --verbose

# Top 10 jogos bons e curtos (padrão)
howl --username meu_id_steam

# Interface visual interativa
howl --username meu_id_steam --tui

# Filtrar por gênero, progresso e fórmula
howl --username meu_id_steam --genre "action,rpg" --not-started --sort quick-wins

# Filtrar por época de lançamento
howl --username meu_id_steam --era "2010-2015,2015-2020"

# Ver o que está disponível no cache
howl --list-genres
howl --list-tags
howl --list-collections
```

Com `STEAM_USERNAME` definido no ambiente, `--username` pode ser omitido.

## Fórmulas de ordenação (`--sort`)

| Nome | Fórmula | Quando usar |
|------|---------|-------------|
| `shortest` | composite / √h | Jogos bons e curtos — default |
| `longest` | composite × √h | Épicos que valem cada hora |
| `rated` | Metacritic puro | Mais aclamados pela crítica |
| `loved` | Steam % positivo | Mais amados pelos jogadores |
| `quick-wins` | composite² / h | Qualidade máxima em menos tempo |
| `hidden-gems` | steam × (1 − mc/100) | Amados pelos players, ignorados pela crítica |
| `composto` | 0.5×mc + 0.5×steam | Média ponderada configurável |

`composite` = média ponderada de Metacritic e Steam reviews (ajuste com `--weight-mc` / `--weight-steam`).

Jogos sem Metacritic ou Steam reviews recebem peso zero naquela fonte (o outro assume 100%).

## Filtros disponíveis

| Flag | Valores | Default |
|------|---------|---------|
| `--sort` | ver tabela acima | `shortest` |
| `--genre` | vírgula-separado | — |
| `--genre-any` | vírgula-separado | — |
| `--exclude-genre` | vírgula-separado | — |
| `--era` | `pre-2005` `2005-2010` `2010-2015` `2015-2020` `2020+` `unknown` | todas |
| `--not-started` | — | — |
| `--in-progress` | — | — |
| `--all-progress` | — | não-zerados |
| `--category` | `all` `singleplayer` `coop` | `all` |
| `--min-hours` / `--max-hours` | horas (HLTB) | — |
| `--collection` | nome da coleção Steam | — |
| `--top` | inteiro | `10` |
| `--show-finished` | — | excluídos |

## TUI (interface visual)

```bash
howl --username meu_id_steam --tui
```

| Tecla | Ação |
|-------|------|
| `f` | Abrir/fechar painel de filtros |
| `g` | Toggle coluna de gêneros |
| `t` | Toggle coluna de categorias Steam |
| `s` | Salvar resultado atual em CSV + Markdown |
| `q` | Sair |

O painel de filtros aplica todas as mudanças em tempo real.

## Cache

Os dados de HLTB, Steam Reviews e detalhes do jogo são cacheados em `games_cache.json` para evitar requisições repetidas. Para atualizar:

```bash
# Rebuscar tudo do zero
howl --username meu_id_steam --refresh

# Preencher campos ausentes em entradas antigas (genres, release_year)
howl --migrate-cache

# Buscar scores IGDB para jogos sem Metacritic (requer IGDB_CLIENT_ID e IGDB_CLIENT_SECRET)
howl --migrate-igdb
```

O `--migrate-cache` é útil se você tinha um cache de versões anteriores que não tinham todos os campos.

O `--migrate-igdb` preenche scores de críticos via IGDB para jogos onde o Steam não retorna Metacritic — útil especialmente para jogos delisted (ex: Deus Ex: Human Revolution original). Pode ser re-rodado a qualquer momento; jogos que já têm dados IGDB no cache são pulados.

## Troubleshooting

**"Username not found on Steam"**
Verifique se a vanity URL está correta. Acesse `https://steamcommunity.com/id/seu_id/` — se redirecionar para seu perfil, está certo.

**Jogos sem Metacritic ou Steam reviews**
Normal — não todos os jogos têm dados. Eles ainda aparecem mas com score 0 em algumas fórmulas. Use `--sort loved` ou `--sort rated` para ver só quem tem dados.

**"0 entradas para migrar"**
O cache já está completo. Se acabou de criar o cache com `howl --verbose`, todos os jogos já saem com todos os campos.

**Cache com poucos jogos**
Se a biblioteca Steam está como privada, a API retorna 0 jogos. Acesse Steam → Perfil → Editar → deixe jogos como público (pode voltar a privado depois).

## Desenvolvimento

```bash
pytest                          # rodar todos os testes
pytest tests/test_score.py -v   # módulo específico
```