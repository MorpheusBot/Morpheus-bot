from config.messages import GlobalMessages


class EmojiMess(GlobalMessages):
    emoji_brief = "Group of commands for getting emojis"
    get_emojis_brief = "Download all emojis and send them as emojis.zip"
    get_emoji_brief = "Show emoji in full size"
    get_sticker_brief = "Download sticker from a specific message"
    invalid_emoji = "Invalid format of emoji"
    add_server_emoji_brief = "Add emoji to server from existing emoji"
    unicode_emoji = "Unicode emojis can't be added as custom emojis"
    emoji_download_err = "Failed to download emoji image"
    emoji_add_success = "Emoji {emoji} added successfully"
    no_stickers_found = "No stickers found in the specified message."
