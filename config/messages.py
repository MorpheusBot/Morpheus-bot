import discord


class CallableString(str):
    to_escape = ["role", "not_role", "line"]

    def __call__(self, *args, **kwargs):
        for arg in self.to_escape:
            if arg in kwargs:
                kwargs[arg] = discord.utils.escape_mentions(kwargs[arg])

        return self.format(**kwargs)


class Formatable(type):
    def __getattribute__(cls, key):
        try:
            val = object.__getattribute__(cls, key)
        except AttributeError:
            try:
                val = super().__getattribute__(key)
            except AttributeError:
                raise AttributeError(f"{cls.__name__} class has no attribute {key}")

        if isinstance(val, str):
            return CallableString(val)

        # If it's a list/tuple of strings, wrap each string element so the
        # returned container still behaves like a sequence of strings but each
        # element is a CallableString (a str subclass) and can be called.
        if isinstance(val, (list, tuple)):
            return [x for x in val]

        return val


class GlobalMessages(metaclass=Formatable):
    Morpheus = [
        "Remember...All I'm Offering Is The Truth. Nothing More.",
        "I Have Dreamed A Dream, But Now That Dream Is Gone From Me.",
        "What Was Said Was For You, And You Alone.",
        "A Sentinel For Every Man, Woman, And Child In Zion. That Sounds Exactly Like The Thinking Of A Machine To Me.",
        "We Are Still Here!",
        "Fate, It Seems, Is Not Without A Sense Of Irony.",
        "Remember...All I'm Offering Is The Truth. Nothing More.",
        "You Have To Understand, Most People Are Not Ready To Be Unplugged...",
        "You Think That's Air You're Breathing Now?",
        "Have You Ever Had A Dream, Neo, That You Were So Sure Was Real?",
        "What You Know You Can't Explain, But You Feel It. You've Felt It Your Entire Life. ",
        "Don't THINK You Are. KNOW You Are.",
        "I Can Only Show You The Door. You're The One That Has To Walk Through It.",
        "He's Beginning To Believe!",
        "You Have To Let It All Go, Neo - Fear, Doubt, And Disbelief. Free Your Mind!",
        "You Take The Red Pill - You Stay In Wonderland, And I Show You How Deep The Rabbit Hole Goes.",
        "I Can Only Show You The Door...",
        "What is real? How do you define real?",
    ]
    morpheus_url = "https://github.com/solumath/Morpheus"
    commands_count = "All commands - **{sum}**\nContext commands - **{context}**\nSlash commands - **{slash}**\nMessage commands - **{message}**\nUser commands - **{user}**"

    not_enough_perms = "You do not have permissions to use this."
    command_on_cooldown = "This command is on cooldown. Please try again in {time}."
    user_not_found = "User could not be found."
    error_happened = "`Errors happen Mr. Anderson`"
    embed_not_author = "You can't interact with this embed, because you are not author."

    channel_history_brief = "Get a channel history with date, content and author."
    channel_history_success = "Accessing history successful, file `{}_history.txt` created."
    channel_history_retrieving_messages = "Retrieving messages from channel {}."

    webhook_backup_brief = "Backups whole channel with webhook."
