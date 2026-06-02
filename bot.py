import os
import math
import logging
import logging.config
from aiohttp import web
from LUCIFER import web_server

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("cinemagoer").setLevel(logging.ERROR)

from pyrogram.errors import BadRequest, Unauthorized
from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, PORT, ADMINS
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
LOGGER = logging.getLogger(__name__)
TIMEZONE = (os.environ.get("TIMEZONE", "Asia/Kolkata"))

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "LUCIFER"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        temp.B_LINK = me.mention
        self.username = '@' + me.username
        curr = datetime.now(timezone(TIMEZONE))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)
        
        if LOG_CHANNEL:
            try:
                await self.send_message(LOG_CHANNEL, text=f"<b>{me.mention} Rᴇsᴛᴀʀᴛᴇᴅ !!\n\n📅 Dᴀᴛᴇ : <code>{date}</code>\n⏰ Tɪᴍᴇ : <code>{time}</code>\n🌐 Tɪᴍᴇᴢᴏɴᴇ : <code>{TIMEZONE}</code>\n\n🉐 Vᴇʀsɪᴏɴ : <code>v{__version__}</code></b>")
            except Unauthorized:
                LOGGER.warning("Bot isn't able to send message to LOG_CHANNEL. Trying Admins...")
                await self.send_to_admins(me, date, time)
            except BadRequest as e:
                LOGGER.error(f"LOG_CHANNEL BadRequest: {e}. Trying Admins...")
                await self.send_to_admins(me, date, time)
            except Exception as e:
                LOGGER.error(f"Unexpected error when sending to LOG_CHANNEL: {e}. Trying Admins...")
                await self.send_to_admins(me, date, time)

    async def send_to_admins(self, me, date, time):
    
        for admin_id in ADMINS:
            try:
                await self.send_message(
                    chat_id=admin_id, 
                    text=f"<b>⚠️ LOG_CHANNEL par message nahi gaya!\n\n{me.mention} Rᴇsᴛᴀʀᴛᴇᴅ !!\n\n📅 Dᴀᴛᴇ : <code>{date}</code>\n⏰ Tɪᴍᴇ : <code>{time}</code>\n🌐 Tɪᴍᴇᴢᴏɴᴇ : <code>{TIMEZONE}</code></b>"
                )
                logging.info(f"Notification successfully sent to Admin PM: {admin_id}")
            except Exception as e:
                LOGGER.error(f"Admin {admin_id} ke PM mein message nahi bheja ja saka: {e}")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
