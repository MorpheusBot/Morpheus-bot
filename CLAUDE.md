# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Morpheus is a Discord bot for a friends server, built with Python 3.12+, discord.py, and PostgreSQL. Music streaming uses Wavelink + Lavalink. The bot is fully async and deployed via Docker Compose.

## Common Commands

### Running the Bot

```bash
# Docker (recommended)
docker compose up -d

# Local dev
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python morpheus.py
```

### Linting

```bash
ruff check .        # lint
ruff format .       # format
codespell .         # spell check
```

Pre-commit hooks run these automatically on commit. Install with:
```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Database Migrations

```bash
alembic upgrade head                                  # apply migrations
alembic revision --autogenerate -m "description"     # generate new migration
```

See `database/README.md` for backup/restore and debug connection instructions.

## Architecture

### Entry Point

`morpheus.py` defines the `Morpheus` class (extends `commands.Bot`). On startup (`setup_hook`) it:
1. Initializes the PostgreSQL database
2. Connects to the Lavalink server (music)
3. Creates an `aiohttp.ClientSession` for API calls
4. Loads all cogs from the `cogs/` directory

### Cog System

All features are implemented as discord.py Cogs in `cogs/`. Each cog directory contains:
- `cog.py` — main logic and command definitions
- `__init__.py` — `setup()` function for cog loading
- `messages.py` — all user-facing strings for that cog
- Optionally: `features.py` (helpers), `views.py` (UI components), `buttons.py`

All cogs inherit from `cogs/base.py`, which provides shared access to bot, config, and cached channel references.

### Configuration

Config is loaded via `config/app_config.py` from `config/config.toml` (copy from `config/config.template.toml`). The config object is accessible throughout cogs via `self.config`. Music server config lives in `config/application.yml`.

### Database Layer

`database/` contains SQLAlchemy models with async support:
- `guild.py` — `GuildDB` (guild settings), `GuildPhraseDB` (custom phrases with optional attachments and user restrictions)
- `voice.py` — `PlaylistDB` (music playlists, per-user or per-guild)
- `database.py` — engine and session management
- `migrations/` — Alembic migration scripts

### Utilities

- `utils/embed.py` — embed builders and `PaginationView` for paginated Discord UI
- `custom/cooldowns.py` — cooldown decorators
- `custom/permission_check.py` — permission verification helpers
- `custom/custom_errors.py` — custom exceptions caught by `cogs/error/`

### Deployment

CI/CD via GitHub Actions:
- `.github/workflows/lint.yml` — runs pre-commit on PRs
- `.github/workflows/deployment.yml` — auto-deploys `master` to production via SSH (bypass with `no-deployment` label)
