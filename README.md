# Morpheus

I Can Only Show You The Door...

Discord bot for managing friends server.

- [discord.py](https://github.com/Rapptz/discord.py) - wrapper for Discord API
- [Docker](https://docs.docker.com) - deployment environment
- PostgreSQL + sqlalchemy - database
- Python 3.12

## Configuration

```bash
cp config/config.template.toml config/config.toml
cp config/application_template.yml config/application.yml
```

Now open the `config.toml` file in your editor. Insert the Discord API:

```
1 [base]
2 default_prefix = '?'
3 key = '<Your Discord API key>'
...
```

> [!WARNING]
> __Be careful.__ Bad things will happen if anyone else gets a possession of this key. Do not share it with anyone, ever!

On the next two lines, insert your Discord user and server ID so you get administrator rights over the bot:

```
4 admin_ids = [<Your Discord user ID>]
5 guild_id = <Your Server ID here>
```

> [Where can I find my User/Server/Message ID?](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)

Then, create the following 5 channels (or use one channel for all of them) on your server and paste their IDs to the config:

```
11 bot_channel = <Channel ID>
12 bot_dev_channel = <Channel ID>
```

> [!CAUTION]
> There are needed some additional steps for permissions and variables.
>
> ```bash
> ./init.sh
> ```

Also don't forget to import credentials for whatever sources you will be using in `config/application.yml`.

(Optional) For some features you will also need to set other config variables, usually they are divided into categories based on cogs.

### Docker setup (recommended)

Install Docker & Docker Compose V2 by going to their [official documentation](https://docs.docker.com/engine/install/). Just select your OS and follow the steps.

> You can also install Docker as a GUI App — Docker Desktop — which includes everything you need.

- If you haven't already, enable `docker` service on startup: `sudo systemctl enable --now docker.service`. Most installers should do that automatically, though.
- To use Docker without `sudo`, you also need to be in `docker` group (eg. `sudo usermod -aG docker $USER && newgrp docker`).
- It's recommended to restart your system at this point (to get all the permissions and other stuff right).

#### a. Dev containers in VS Code (one click run) — preferred option

If you are using VS Code, you can simply run Rubbergod by using the [Dev containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.
Either by clicking on a notification or by clicking on arrows in bottom left corner (Open a Remote Window) and choosing `Reopen in container`.

#### b. Docker Compose CLI — if you don't use VS Code

This command should do the trick:

```bash
docker compose up
```

Docker will download all the necessary stuff and run the container. If you did everything correctly, bot will connect to the DB, load all the extensions and print `Logged in as` at the end. It will also send statistics emoji to the `#bot-dev-channel` if you configured one. You're now all set!

## Development

If you didn't run the container in detached mode, just press `Ctrl+C` to stop it.

Try to tweak some command a little bit and run the bot again, this time you can try to open it in detached mode so it won't block your terminal:

```bash
docker compose up -d
```

To stop the detached container, use this command:

```bash
docker compose down
```

### Tips

#### Debugging

Logs are stored in `morpheus.log` file or `logs` directory. Errors are printed to the console, morpheus.log and sent to the `#bot-dev-channel` if you configured one.

Database-related tips can be found in [database README](database/README.md).

## Pre-commit (useful for dev)

We have setup pre-commit in this repository. To use it use these commands:

```bash
pip install -r requirements-dev.txt
pre-commit install
```
