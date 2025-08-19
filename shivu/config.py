class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "1318826936"
    sudo_users = "5821905026", "1318826936"
    GROUP_ID = "-1002356385851"
    TOKEN = "8345134806:AAGc_ygSXBH2rZz7omtpjytraXj_Yyrbr-s"
    mongo_url = "mongodb+srv://wanglin:wanglin@wanglin.ppt93bd.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://files.catbox.moe/sygsr7.jpg", "https://files.catbox.moe/8mpep6.jpg"]
    SUPPORT_CHAT = "sasukemusicsupportchat"
    UPDATE_CHAT = "sasukevipmusicbotsupport"
    BOT_USERNAME = "charactercollections_bot"
    CHARA_CHANNEL_ID = "-1002459775779"
    api_id = "29758428"
    api_hash = "51f9369e03f78674ca21aee8dfd1c842"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
