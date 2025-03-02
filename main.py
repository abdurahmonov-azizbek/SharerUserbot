import json
from pyrogram import Client, filters
import re


def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "admin_id": 7305090563,  
            "source_chats": [],
            "target_chat": "",
            "filters": {
                "keywords": [],
                "types": [],
                "remove_types": [],
                "forwarded_from": False,
                "append_keyword": ""
            }
        }

def save_settings(data):
    with open("settings.json", "w") as f:
        json.dump(data, f, indent=4)

settings = load_settings()

api_id = 26265257
api_hash = "d82296fe28dd3589b08624b04449dbf8"
app = Client("userbot", api_id, api_hash)

@app.on_message(filters.chat(settings["source_chats"]))
async def forward_message(client, message):
    filters_config = settings["filters"]
    text = message.text or message.caption or ""

    # 1️⃣ Check keyword filters (skip if it contains blocked keywords)
    for kw in filters_config["keywords"]:
        if str(kw).lower() in text.lower():
            return  # Skip the message if it contains blocked keywords

    # 2️⃣ Check spammed types (skip if it matches a blocked type)
    spammed_types = filters_config["types"]
    if ("text" in spammed_types and message.text) or \
       ("link" in spammed_types and has_link(text)) or \
       ("file" in spammed_types and message.document) or \
       ("photo" in spammed_types and message.photo) or \
       ("video" in spammed_types and message.video) or \
       ("location" in spammed_types and message.location) or \
       ("contact" in spammed_types and message.contact):
        return  # Skip the message if it matches a blocked type

    # 3️⃣ Apply append_keyword
    append_keyword = filters_config["append_keyword"]
    if append_keyword and text:
        text += f"\n\n{append_keyword}"

    remove_types = filters_config["remove_types"]
    if "link" in remove_types:
        text = remove_links(text)
    if "photo" in remove_types:
        message.photo = None

    # 4️⃣ Forward message with or without "Forwarded from"
    disable_forward_info = filters_config.get("forwarded_from", False)

    if not disable_forward_info:
        # Handle photo with caption
        if message.photo:
            await client.send_photo(settings["target_chat"], message.photo.file_id, caption=text)
        # Handle text messages
        elif message.text:
            await client.send_message(settings["target_chat"], text)
        # Handle other message types
        elif message.video:
            await client.send_video(settings["target_chat"], message.video.file_id, caption=text)
        elif message.document:
            await client.send_document(settings["target_chat"], message.document.file_id, caption=text)
        elif message.audio:
            await client.send_audio(settings["target_chat"], message.audio.file_id, caption=text)
        elif message.voice:
            await client.send_voice(settings["target_chat"], message.voice.file_id, caption=text)
        elif message.sticker:
            await client.send_sticker(settings["target_chat"], message.sticker.file_id)
        elif message.contact:
            await client.send_contact(settings["target_chat"], phone_number=message.contact.phone_number, first_name=message.contact.first_name)
        elif message.location:
            await client.send_location(settings["target_chat"], latitude=message.location.latitude, longitude=message.location.longitude)
    else:
        await message.forward(settings["target_chat"])

def has_link(text):
    """
    Xabarda link bor-yo'qligini aniqlaydi.
    :param text: Xabar matni
    :return: True (agar link bo'lsa), False (agar link bo'lmasa)
    """
    # Telegram username linklari (@username)
    telegram_username_pattern = r"@[a-zA-Z0-9_]{5,}"  # @ belgisi va kamida 5 belgi

    # Oddiy URL manzillar (https://, http:// yoki www. bilan boshlanadiganlar)
    url_pattern = r"(https?://[^\s]+|www\.[^\s]+)"  # http://, https:// yoki www.

    # Barcha linklarni regex orqali aniqlash
    if re.search(telegram_username_pattern, text) or re.search(url_pattern, text):
        return True
    return False

def remove_links(text):
    """
    Xabardagi barcha linklarni o'chirib tashlaydi.
    :param text: Xabar matni
    :return: Linklarsiz yangi matn
    """
    # Telegram username linklari (@username)
    telegram_username_pattern = r"@[a-zA-Z0-9_]{5,}"  # @ belgisi va kamida 5 belgi

    # Oddiy URL manzillar (https://, http:// yoki www. bilan boshlanadiganlar)
    url_pattern = r"(https?://[^\s]+|www\.[^\s]+)"  # http://, https:// yoki www.

    # Barcha linklarni regex orqali o'chirish
    text = re.sub(telegram_username_pattern, "", text)  # @username larni o'chirish
    text = re.sub(url_pattern, "", text)  # URL manzillarni o'chirish

    # Qo'shimcha: Agar linklarni o'chirish natijasida ortiqcha bo'shliqlar qolsa, ularni ham tozalash
    # text = " ".join(text.split())  # Ortiqcha bo'shliqlarni olib tashlash

    return text

# Admin buyruqlari  
@app.on_message(filters.command("addsource") & filters.user(settings["admin_id"]))
async def add_source(client, message):
    chat_id = message.text.split(" ")[1]
    if chat_id not in settings["source_chats"]:
        settings["source_chats"].append(chat_id)
        save_settings(settings)
        await message.reply_text(f"✅ {chat_id} manba sifatida qo'shildi!")

@app.on_message(filters.command("delsource") & filters.user(settings["admin_id"]))
async def del_source(client, message):
    chat_id = message.text.split(" ")[1]
    if chat_id in settings["source_chats"]:
        settings["source_chats"].remove(chat_id)
        save_settings(settings)
        await message.reply_text(f"❌ {chat_id} manbadan olib tashlandi!")

@app.on_message(filters.command("settarget") & filters.user(settings["admin_id"]))
async def set_target(client, message):
    chat_id = message.text.split(" ")[1]
    settings["target_chat"] = chat_id
    save_settings(settings)
    await message.reply_text(f"🎯 Target chat {chat_id} qilib o'rnatildi!")

@app.on_message(filters.command("settings"))
async def get_settings(client, message):
    txt = f"Source chats: {settings['source_chats']}\n" \
          f"Target chat: {settings['target_chat']}\n" \
          f"Spam keywords: {settings["filters"]["keywords"]}\n" \
          f"Spam types: {settings["filters"]["types"]}\n" \
          f"Types for remove: {settings["filters"]["remove_types"]}\n" \
          f"Append keyword: {settings["filters"]["append_keyword"]}" 
    
    await message.reply_text(txt)

@app.on_message(filters.command("getcurtarget"))
async def get_current_target(client, message):
    await message.reply_text(f"Current target chat👉 {settings["target_chat"]}");

@app.on_message(filters.command("get_message_types"))
async def get_message_types(client, message):
    await message.reply_text(f"text\nlink\nfile\nphoto\nvideo\nlocation\ncontact")

@app.on_message(filters.command("help"))
async def help(client, message):
    txt = "/settings - current settings\n" \
        + "/addsource @chat_username - add source chat\n" \
        + "/delsource @chat_username - delete source chat\n" \
        + "/settarget @chat_username - set target chat\n" \
        + "/getcurtarget - current target chat\n" \
        + "/get_message_types - get all message types in telegram\n" \
        + "/add_keyword keyword - add to spam keywords\n" \
        + "/del_keyword keyword - remove from spam keywords\n" \
        + "/add_spam_type type - add type to spam types\n" \
        + "/del_spam_type type  - delete type from spam types\n" \
        + "/set_append keyword - set keyword for append\n" \
        + "/del_removetype type - add type for remove\n" \
        + "/add_removetype type - remove type from remove_types\n"
    
    await message.reply_text(txt)

@app.on_message(filters.command("set_append"))
async def add_spam_type(client, message):
    data = message.text.split(" ")
    data = " ".join(data[1:])
    settings["filters"]["append_keyword"] = data
    save_settings(settings)
    await message.reply_text(f"✅")

@app.on_message(filters.command("add_spam_type"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["types"].append(data)
    save_settings(settings)
    await message.reply_text(f"{data} - added to spam types!")

@app.on_message(filters.command("del_spam_type"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["types"].remove(data)
    save_settings(settings)
    await message.reply_text(f"{data} - removed from spam types!")

@app.on_message(filters.command("add_removetype"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["remove_types"].append(data)
    save_settings(settings)
    await message.reply_text(f"{data} - added to remove types!")

@app.on_message(filters.command("del_removetype"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["remove_types"].remove(data)
    save_settings(settings)
    await message.reply_text(f"{data} - removed from remove types!")

@app.on_message(filters.command("add_keyword"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["keywords"].append(data)
    save_settings(settings)
    await message.reply_text(f"{data} - added to keywords!")

@app.on_message(filters.command("del_keyword"))
async def add_spam_type(client, message):
    data = message.text.split(" ")[1]
    settings["filters"]["keywords"].remove(data)
    save_settings(settings)
    await message.reply_text(f"{data} - removed from keywords!")


app.run()
