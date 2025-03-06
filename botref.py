import json
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command

# Configuración del bot con variables de entorno
TOKEN = "7816805012:AAHp9ooQMRG9fQimK5NBuyywkckEkcMDyDY"
CANAL_FREE_ID = int(os.getenv("CANAL_FREE_ID", "-1002482424183"))
CANAL_VIP_ID = int(os.getenv("CANAL_VIP_ID", "-1002117720163"))
ENLACE_VIP = os.getenv("ENLACE_VIP", "https://t.me/+FS55S5eOvpQ0MmUx")

# Inicializar el bot y el dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Archivos JSON
USUARIOS_FILE = "usuarios.json"
REFERIDOS_FILE = "referidos.json"

# 📌 Funciones para manejar datos
def cargar_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# 📌 Comando /start → Guarda automáticamente el ID del usuario
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username

    usuarios = cargar_json(USUARIOS_FILE)

    if username:
        usuarios[username.lower()] = user_id  # Guardar en minúsculas para evitar errores
        guardar_json(USUARIOS_FILE, usuarios)

    await message.answer(
        "👋 ¡Hola! Este es el bot de referidos.\n\n"
        "✅ Para sumar referidos, envía un mensaje diciendo:\n"
        "`He metido a @UsuarioDeTelegram`\n\n"
        "📌 Cuando llegues a 15 referidos, recibirás acceso al canal VIP."
    )

# 📌 Función para verificar si un usuario está en el canal
async def verificar_usuario_en_canal(user_id):
    try:
        user_info = await bot.get_chat_member(CANAL_FREE_ID, user_id)
        return user_info.status in ["member", "administrator", "creator"]
    except:
        return False

# 📌 Obtener `user_id` si el usuario no ha interactuado con el bot
async def obtener_id_usuario(username):
    usuarios = cargar_json(USUARIOS_FILE)

    # 📌 1️⃣ Si el username ya está en la base de datos, lo usamos
    if username.lower() in usuarios:
        return usuarios[username.lower()]

    # 📌 2️⃣ Intentar obtener el user_id desde el canal
    try:
        chat_member = await bot.get_chat_member(CANAL_FREE_ID, username)
        user_id = str(chat_member.user.id)
        
        # Guardar en la base de datos para futuras referencias
        usuarios[username.lower()] = user_id
        guardar_json(USUARIOS_FILE, usuarios)
        
        return user_id
    except:
        return None  # No se pudo obtener el ID

# 📌 Manejo de referidos con verificación automática de ID en tiempo real
@dp.message(F.text.startswith("He metido a @"))
async def manejar_referido(message: Message):
    usuario_id = str(message.from_user.id)
    nombre_referido = message.text[11:].strip().replace("@", "").lower()

    # Obtener el `user_id` del referido desde la base de datos o el canal
    referido_id = await obtener_id_usuario(nombre_referido)

    if not referido_id:
        await message.answer(
            f"⚠️ No pude obtener el ID de @{nombre_referido}. "
            "El usuario debe enviar `/start` al bot antes de ser referido."
        )
        return

    # Verificar si el usuario está en el canal
    esta_en_canal = await verificar_usuario_en_canal(referido_id)

    if not esta_en_canal:
        await message.answer(f"⚠️ @{nombre_referido} no está en el canal free. Asegúrate de que se haya unido antes de referirlo.")
        return

    # Agregar referido a la base de datos
    referidos = cargar_json(REFERIDOS_FILE)

    if usuario_id not in referidos:
        referidos[usuario_id] = []

    if referido_id not in referidos[usuario_id]:
        referidos[usuario_id].append(referido_id)

    guardar_json(REFERIDOS_FILE, referidos)

    # Contar referidos y dar acceso al VIP si corresponde
    total_referidos = len(referidos[usuario_id])

    if total_referidos < 15:
        faltan = 15 - total_referidos
        await message.answer(f"✅ @{nombre_referido} ha sido agregado a tu lista de referidos.\n\n📌 Te faltan {faltan} personas para acceder al canal VIP.")
    else:
        await message.answer(f"🎉 ¡Felicidades! Has alcanzado los 15 referidos.\n\n🔥 Aquí tienes tu acceso al canal VIP:\n{ENLACE_VIP}")

# 📌 Iniciar el bot
async def main():
    print("🤖 Bot iniciado correctamente...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
