from config.messages import GlobalMessages


class NameDayMess(GlobalMessages):
    name_day_cz = "Dnes má svátek {name}."
    name_day_cz_brief = "Zobrazí dnešní svátek nebo vyhledá, kdy má dané jméno svátek."
    name_day_cz_param = "Jméno k vyhledání (pokud není zadáno, zobrazí dnešní svátek)"
    name_day_sk = "Dnes má meniny {name}."
    name_day_sk_brief = "Zobrazí dnešné meniny alebo vyhľadá, kedy má dané meno meniny."
    name_day_sk_param = "Meno na vyhľadanie (ak nie je zadané, zobrazí dnešné meniny)"

    # Holiday messages
    holiday_cz = "Dnes si připomínáme {holiday}."
    holiday_sk = "Dnes si pripomíname {holiday}."

    # Search results
    name_found_cz = "**{name}** má svátek {dates}"
    name_not_found_cz = "Jméno **{name}** nebylo nalezeno."
    name_found_sk = "**{name}** má meniny {dates}"
    name_not_found_sk = "Meno **{name}** nebolo nájdené."

    # Daily announcement
    daily_format = "{cz}\n{sk}"
