import json
from pyrogram import Client, filters


def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "admin_id": 7305090563,  # Admin ID
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
        if kw in text:
            return  

    # 2️⃣ Check spammed types (skip if it matches a blocked type)
    spammed_types = filters_config["types"]
    if ("text" in spammed_types and message.text) or \
       ("link" in spammed_types and message.entities) or \
       ("file" in spammed_types and message.document) or \
       ("photo" in spammed_types and message.photo) or \
       ("video" in spammed_types and message.video) or \
       ("location" in spammed_types and message.location) or \
       ("contact" in spammed_types and message.contact):
        return  

    # 3️⃣ Check remove_types (remove only specific parts)
    remove_types = filters_config["remove_types"]
    keep_text = True  # We always keep text unless it's in spammed_types

    if "photo" in remove_types and message.photo:
        message.photo = None
    if "video" in remove_types and message.video:
        message.video = None
    if "file" in remove_types and message.document:
        message.document = None
    if "audio" in remove_types and message.audio:
        message.audio = None
    if "voice" in remove_types and message.voice:
        message.voice = None
    if "sticker" in remove_types and message.sticker:
        message.sticker = None
    if "contact" in remove_types and message.contact:
        message.contact = None
    if "location" in remove_types and message.location:
        message.location = None
    if "text" in remove_types and message.text:
        keep_text = False  # If "text" is in remove_types, discard the text

    # If everything is removed, don't send anything
    if not (keep_text or message.photo or message.video or message.document or message.audio or message.voice or message.sticker or message.contact or message.location):
        return  

    # 4️⃣ Apply append_keyword
    append_keyword = filters_config["append_keyword"]
    if append_keyword and keep_text:
        text += f"\n\n{append_keyword}"

    # 5️⃣ Forward message with or without "Forwarded from"
    disable_forward_info = filters_config.get("forwarded_from", False)

    if not disable_forward_info:
        if keep_text:
            await client.send_message(settings["target_chat"], text)
        if message.photo:
            await client.send_photo(settings["target_chat"], message.photo.file_id, caption=text if keep_text else None)
        if message.video:
            await client.send_video(settings["target_chat"], message.video.file_id, caption=text if keep_text else None)
        if message.document:
            await client.send_document(settings["target_chat"], message.document.file_id, caption=text if keep_text else None)
        if message.audio:
            await client.send_audio(settings["target_chat"], message.audio.file_id, caption=text if keep_text else None)
        if message.voice:
            await client.send_voice(settings["target_chat"], message.voice.file_id, caption=text if keep_text else None)
        if message.sticker:
            await client.send_sticker(settings["target_chat"], message.sticker.file_id)
        if message.contact:
            await client.send_contact(settings["target_chat"], phone_number=message.contact.phone_number, first_name=message.contact.first_name)
        if message.location:
            await client.send_location(settings["target_chat"], latitude=message.location.latitude, longitude=message.location.longitude)
    else:
        await message.forward(settings["target_chat"])

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
        + "/addsource [@chat_username] - add source chat\n" \
        + "/delsource [@chat_username] - delete source chat\n" \
        + "/settarget [@chat_username] - set target chat\n" \
        + "/getcurtarget - current target chat\n" \
        + "/get_message_types - get all message types in telegram\n" \
        + "/add_spam_type [type name] - add type to spam types\n" \
        + "/del_spam_type [type name] - delete type from spam types\n" \
        + "/set_append [keyword] - set keyword for append\n" \
        + "/del_removetype [type] - add type for remove\n" \
        + "/add_removetype [type] - remove type from remove_types\n"
    
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



app.run()
