# Publicação no PyPI — howl-cli

## Status

- [ ] pyproject.toml completo
- [ ] LICENSE criado
- [ ] Trusted Publisher configurado no PyPI
- [ ] workflow publish.yml criado
- [ ] primeira release publicada

---

## 1. Nome do pacote

`howl` está tomado no PyPI. Nome escolhido: **`howl-cli`**.

O comando instalado continua `howl` (definido em `[project.scripts]`).
Ou seja: `pip install howl-cli` → `howl` no terminal.

Verificar disponibilidade antes de prosseguir:
```bash
pip index versions howl-cli 2>&1 | head -3
# "ERROR: No matching distribution" = disponível
```

---

## 2. pyproject.toml — campos que faltam

Adicionar ao bloco `[project]`:

```toml
[project]
name = "howl-cli"
version = "0.2.0"
description = "HOWL — ranks your Steam backlog by quality × playtime."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [
    { name = "Alberto de Sá Cavalcanti de Albuquerque", email = "albertoalbuquerque01@gmail.com" },
]
keywords = ["steam", "gaming", "backlog", "howlongtobeat", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Games/Entertainment",
]

[project.urls]
Homepage = "https://github.com/albertosca/howl"
Repository = "https://github.com/albertosca/howl"
"Bug Tracker" = "https://github.com/albertosca/howl/issues"
```

Manter tudo o mais (dependencies, scripts, optional-dependencies) igual.

---

## 3. LICENSE

Criar `LICENSE` na raiz com o texto MIT padrão:

```
MIT License

Copyright (c) 2026 Alberto de Sá Cavalcanti de Albuquerque

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. Trusted Publisher (OIDC) — sem token de longa duração

Trusted Publisher permite que o GitHub Actions publique no PyPI via OIDC — sem gerar nem armazenar `PYPI_API_TOKEN` nos secrets do repo. É a abordagem recomendada pelo PyPI desde 2023.

### 4a. Criar conta e projeto no PyPI

1. Criar conta em https://pypi.org (se não tiver)
2. Ativar 2FA (obrigatório para publicar)
3. Ir em **Account Settings → Publishing → Add a new pending publisher**
4. Preencher:
   - PyPI project name: `howl-cli`
   - GitHub repo owner: `albertosca`
   - GitHub repo name: `howl`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi` (deixar em branco ou usar "pypi")

Isso cria um "Pending Publisher" — o projeto no PyPI é criado automaticamente na primeira publicação bem-sucedida.

### 4b. Criar environment no GitHub

1. Ir em https://github.com/albertosca/howl/settings/environments
2. Criar environment chamado **`pypi`**
3. Opcional: adicionar regra "Required reviewers" (você mesmo) para aprovar antes de publicar

---

## 5. Workflow de publicação

Criar `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # necessário para Trusted Publisher (OIDC)

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Build
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

Sem secrets necessários — o OIDC cuida da autenticação.

---

## 6. Estratégia de versão

Versão manual por enquanto (sem automação de bump). Fluxo:

1. Editar `version` no `pyproject.toml` (ex: `"0.2.0"`)
2. Commitar: `chore: bump version to 0.2.0`
3. Criar release no GitHub: **Releases → Draft a new release → Tag: `v0.2.0`**
4. Publicar a release → dispara o workflow → publica no PyPI

Semver: `MAJOR.MINOR.PATCH`
- PATCH: bugfixes
- MINOR: nova feature (--refresh-all, IGDB improvements, etc.)
- MAJOR: quebra de compatibilidade (mudança de cache format, API keys, etc.)

Versão atual do código: `0.1.0` → próxima release: `0.2.0` (várias features desde 0.1).

---

## 7. Checklist de publicação — primeira vez

```
[ ] pip index versions howl-cli  → confirmar nome disponível
[ ] Atualizar pyproject.toml (name, version, authors, license, readme, classifiers, urls)
[ ] Criar LICENSE
[ ] Criar .github/workflows/publish.yml
[ ] Commitar e pushar
[ ] Criar conta PyPI + 2FA
[ ] Configurar Trusted Publisher no PyPI (pending publisher)
[ ] Criar environment "pypi" no GitHub
[ ] Criar release v0.2.0 no GitHub → workflow publica automaticamente
[ ] Verificar: pip install howl-cli && howl --help
```

---

## 8. Instalação para usuários (após publicar)

```bash
pip install howl-cli
howl --help
```

Ou via pipx (recomendado para CLIs):
```bash
pipx install howl-cli
howl --help
```

---

## 9. Divulgação

- README.md: adicionar badge `[![PyPI](https://img.shields.io/pypi/v/howl-cli)](https://pypi.org/project/howl-cli/)`
- README.md: substituir `pip install git+https://github.com/albertosca/howl.git` por `pip install howl-cli`
- README.pt-BR.md: idem

Homebrew tap: esforço alto, vale só se a base de usuários crescer. Deixar para depois.
