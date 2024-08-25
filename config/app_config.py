import toml


def get_attr(toml_dict: dict, section: str, attr_key: str):
    """
    Helper method for getting values from config override or config template.
    """
    try:
        return toml_dict[section][attr_key]
    except KeyError:
        return toml.load("config/config.template.toml", _dict=dict)[section][attr_key]


def eval_channels(toml_dict: dict, channels: list):
    """
    Evaluate channel 'config variable name' to ID
    """
    for idx, channel_name in enumerate(channels):
        if isinstance(channel_name, str):
            channels[idx] = get_attr(toml_dict, "channels", channel_name)
    return channels


class Config:
    """
    Wrapper class for Config and config template.\n
    It checks value from config override and if not exists that will be take from config template.
    """

    toml_dict: dict = toml.load("config/config.toml", _dict=dict)

    # Authorization
    key: str = get_attr(toml_dict, "base", "key")

    # Base information
    admin_ids: list[int] = get_attr(toml_dict, "base", "admin_ids")
    guild_id: int = get_attr(toml_dict, "base", "guild_id")
    default_prefix: str = get_attr(toml_dict, "base", "default_prefix")

    extensions: list[str] = get_attr(toml_dict, "extensions", "extensions")

    # database
    db_string: str = get_attr(toml_dict, "database", "db_string")

    # Special channel IDs
    bot_dev_channel: int = get_attr(toml_dict, "channels", "bot_dev_channel")
    bot_channel: int = get_attr(toml_dict, "channels", "bot_channel")
    thread_channels: list[int] = get_attr(toml_dict, "channels", "thread_channels")
    threads_with_reaction: list[int] = get_attr(toml_dict, "channels", "threads_with_reaction")
    name_day_channels: int = get_attr(toml_dict, "channels", "name_day_channels")
    nasa_channels: list[int] = get_attr(toml_dict, "channels", "nasa_channels")
    gay_channel: int = get_attr(toml_dict, "channels", "gay_channel")
    webhook: int = get_attr(toml_dict, "channels", "webhook")

    allowed_channels: list[int] = eval_channels(toml_dict, get_attr(toml_dict, "channels", "allowed_channels"))

    # Memes
    jany: int = get_attr(toml_dict, "memes", "jany")
    ilbinek: int = get_attr(toml_dict, "memes", "ilbinek")

    # Weather
    weather_token: str = get_attr(toml_dict, "weather", "token")

    # NASA
    nasa_token: str = get_attr(toml_dict, "nasa", "token")


config = Config()


def load_config():
    global config
    config = Config()
