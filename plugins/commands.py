# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from plugins.users_api import get_user, update_user_info
from plugins.database import get_file_details
from pyrogram.errors import ChatAdminRequired, FloodWait, UserNotParticipant
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
from config import *
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}

# Restriction Logic from Config (Default is True)
PROTECT = environ.get('PROTECT_CONTENT', "True")
IS_PROTECT = True if PROTECT.lower() in ["true", "yes", "1"] else False

# Force Subscribe Function
async def is_subscribed(client, message):
    if not AUTH_CHANNEL:
        return True
    try:
        user = await client.get_chat_member(AUTH_CHANNEL, message.from_user.id)
        if user.status == enums.ChatMemberStatus.BANNED:
            await message.reply_text("Sorry, you are banned from using me.")
            return False
        return True
    except UserNotParticipant:
        buttons = [[
            InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]]
        if message.command and len(message.command) > 1:
            buttons.append([InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={message.command[1]}")])
        
        await message.reply_text(
            text=f"<b>Hello {message.from_user.mention},\n\nYou must join our backup channel to use this bot and access files.\n\nPlease join and try again!</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False
    except Exception as e:
        logger.error(e)
        return True

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

# Status Command (নতুন যুক্ত করা হয়েছে)
@Client.on_message(filters.command("status") & filters.incoming)
async def status_handler(client, message):
    users_count = await db.total_users_count()
    await message.reply_text(
        text=f"<b>📊 Bot Status</b>\n\nTotal Users: <code>{users_count}</code>\nUptime: <code>Running on Koyeb</code>",
        quote=True
    )

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await is_subscribed(client, message):
        return

    username = (await client.get_me()).username
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))
    
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/SGBACKUP')
            ],[
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/SGBACKUP'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/SGBACKUP')
            ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        if CLONE_MODE == True:
            buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = (await client.get_me()).mention
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, me2),
            reply_markup=reply_markup
        )
        return

    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    
    if data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(text="<b>Invalid link or Expired link !</b>", protect_content=IS_PROTECT)
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                protect_content=IS_PROTECT
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(text="<b>Invalid link or Expired link !</b>", protect_content=IS_PROTECT)
            
    elif data.split("-", 1)[0] == "BATCH":
        if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
            btn = [[
                InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
            ],[
                InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
            ]]
            await message.reply_text(
                text="<b>You are not verified !\nKindly verify to continue !</b>",
                protect_content=IS_PROTECT,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
        sts = await message.reply("**🔺 ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
            
        filesarr = []
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                if STREAM_MODE == True:
                    user_id = message.from_user.id
                    username_mention =  message.from_user.mention 

                    log_msg = await client.send_cached_media(
                        chat_id=LOG_CHANNEL,
                        file_id=msg.get("file_id"),
                    )
                    fileName = {quote_plus(get_name(log_msg))}
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
 
                    await log_msg.reply_text(
                        text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username_mention} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                        quote=True,
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                                                            InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)]])
                    )
                if STREAM_MODE == True:
                    button = [[
                        InlineKeyboardButton("🚀 Fast Download 🚀", url=download),
                        InlineKeyboardButton('🖥️ Watch online 🖥️', url=stream)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup=InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                
                msg_sent = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=IS_PROTECT,
                    reply_markup=reply_markup
                )
                filesarr.append(msg_sent)
                
            except FloodWait as e:
                await asyncio.sleep(e.x)
                msg_sent = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=IS_PROTECT,
                    reply_markup=reply_markup
                )
                filesarr.append(msg_sent)
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        
        await sts.delete()
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            for x in filesarr:
                try:
                    await x.delete()
                except:
                    pass
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
        return

    # Single File Logic
    files_ = await get_file_details(file_id)           
    if not files_:
        try:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        except:
            return await message.reply('No such file exist.')

        if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
            btn = [[
                InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
            ],[
                InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
            ]]
            await message.reply_text(
                text="<b>You are not verified !\nKindly verify to continue !</b>",
                protect_content=IS_PROTECT,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            return
        
        try:
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=IS_PROTECT,  
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = '@SGBACKUP  ' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), file.file_name.split()))
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    pass
            
            await msg.edit_caption(f_caption)
            
            g = None
            if STREAM_MODE == True:
                g = await msg.reply_text(
                    text=f"**•• ʏᴏᴜ ᴄᴀɴ ɢᴇɴᴇʀᴀᴛᴇ ᴏɴʟɪɴᴇ sᴛʀᴇᴀᴍ ʟɪɴᴋ ᴏғ ʏᴏᴜʀ ғɪʟᴇ ᴀɴᴅ ᴀʟsᴏ ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ғɪʟᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ 👇**",
                    quote=True,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Fast Download / Watch Online🖥️', callback_data=f'generate_stream_link:{file_id}')]])
                )
            
            # Single File Auto-delete Notification (ফিক্স করা হয়েছে)
            if AUTO_DELETE_MODE == True:
                k = await client.send_message(
                    chat_id = message.from_user.id, 
                    text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u></b> 🫥 (Due to Copyright Issues).\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>"
                )
                await asyncio.sleep(AUTO_DELETE_TIME)
                try: await msg.delete()
                except: pass
                if g: 
                    try: await g.delete()
                    except: pass
                await k.edit_text("<b>Your File/Video is successfully deleted!!!</b>")
            return
        except Exception as e:
            logger.error(e)
            return await message.reply('No such file exist.')

    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            f_caption=f_caption
            
    if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
        ],[
            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            protect_content=IS_PROTECT,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    x = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=IS_PROTECT,
    )
    
    g = None
    if STREAM_MODE == True:
        g = await x.reply_text(
            text=f"**•• ʏᴏᴜ ᴄᴀɴ ɢᴇɴᴇʀᴀᴛᴇ ᴏɴʟɪɴᴇ sᴛʀᴇᴀᴍ ʟɪɴᴋ ᴏғ ʏᴏᴜʀ ғɪʟᴇ ᴀɴᴅ ᴀʟsᴏ ғᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ ғᴏʀ ʏᴏᴜʀ ғɪʟᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ 👇**",
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Fast Download / Watch Online🖥️', callback_data=f'generate_stream_link:{file_id}')]])
        )
    
    # Single File Auto-delete Notification (ফিক্স করা হয়েছে)
    if AUTO_DELETE_MODE == True:
        k = await client.send_message(
            chat_id = message.from_user.id, 
            text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u></b> 🫥 (Due to Copyright Issues).\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>"
        )
        await asyncio.sleep(AUTO_DELETE_TIME)
        try: await x.delete()
        except: pass
        if g:
            try: await g.delete()
            except: pass
        await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
