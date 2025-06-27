import gettext

lang = None

if lang:
    t = gettext.translation(
        "message",
        localedir="locale",
        languages=[lang],
        fallback=True
    )
else:
    t = gettext.NullTranslations()
_ = t.gettext