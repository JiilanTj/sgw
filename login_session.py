from telethon import TelegramClient, events, Button
import os

# Ganti dengan API ID dan API Hash Anda
api_id = 29997622
api_hash = '3e3586f0e43eada49d530bce9549213f'

# Token Bot Telegram Anda
bot_token = '7078440635:AAEIFlsA-7rBS1hbOA1nKBMk6FNjbhteJ5g'

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
session_client = None
sender_user = None  # Variabel global untuk menyimpan pengguna yang memberikan perintah /login


@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    # Mendapatkan daftar file sesi di direktori saat ini
    session_files = [f for f in os.listdir('.') if f.endswith('.session')]

    if not session_files:
        await event.respond("Tidak ada file sesi yang ditemukan di direktori saat ini.")
        return

    buttons = []
    for i, session_file in enumerate(session_files, start=1):
        try:
            file_parts = session_file.split('_')
            if len(file_parts) < 2:
                phone_number = "Nama file tidak valid"
            else:
                phone_number = file_parts[1].split('.')[0]
        except IndexError:
            phone_number = "Nama file tidak valid"

        buttons.append([Button.inline(f"{i}. {phone_number}", data=f"login_{i}")])

    await event.respond("Daftar file sesi:", buttons=buttons)


@bot.on(events.CallbackQuery(data=lambda data: data.startswith(b'login_')))
async def callback_login_handler(event):
    global session_client, sender_user  # Menggunakan session_client dan sender_user global
    sender_user = await event.get_sender()  # Mendapatkan informasi pengguna yang memberikan perintah /login

    choice = int(event.data.decode('utf-8').split('_')[1])

    # Mendapatkan daftar file sesi di direktori saat ini
    session_files = [f for f in os.listdir('.') if f.endswith('.session')]

    if choice < 1 or choice > len(session_files):
        await event.respond("Pilihan tidak valid.")
        return

    selected_session_file = session_files[choice - 1]
    phone_number = selected_session_file.split('_')[1].split('.')[0]
    session_client = TelegramClient(selected_session_file, api_id, api_hash)

    # Memulai sesi
    await session_client.start()
    await event.respond(f"Sesi untuk nomor {phone_number} dimulai.")

    # Menampilkan informasi akun
    me = await session_client.get_me()
    account_info = (
        "Logged in as:\n"
        f"Username = {me.username}\n"
        f"First name = {me.first_name}\n"
        f"Last name = {me.last_name}\n"
        "Password = (Isi dengan password Login apabila user menggunakan Password di Session)"
    )
    await event.respond(account_info)

    # Menerima pesan baru
    @session_client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        global sender_user  # Menggunakan sender_user global
        chat_title = event.chat.title if event.chat else "Pesan Pribadi"
        message_text = f"Pesan baru dari {chat_title}: {event.message.text}"
        if sender_user:
            await bot.send_message(sender_user, message_text)

    await session_client.run_until_disconnected()


@bot.on(events.NewMessage(pattern='/exit'))
async def exit_handler(event):
    global session_client, sender_user

    if session_client is None:
        await event.respond("Tidak ada sesi aktif yang berjalan.")
        return

    if event.sender_id != sender_user.id:
        await event.respond("Anda tidak memiliki izin untuk mengakhiri sesi ini.")
        return

    await session_client.disconnect()
    session_client = None
    sender_user = None

    await event.respond("Sesi telah diakhiri.")
    if sender_user:
        await bot.send_message(sender_user, "Telah keluar dari Sesi")


if __name__ == '__main__':
    print("Bot Started\nPolling...")
    bot.run_until_disconnected()
