# ppt_bot_sqlite.py — Juego PPT con SQLite

import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = '7568912065:AAE2GwT-lhkPKk3EyPL6xzQzaI8k4FCu_Ow'
GRUPO_ID = -1001922181838
TEMA_ID = 44952

import os

# --- Configuración base de datos ---
print("📁 Base de datos guardada en:", os.path.abspath("ppt.db"))
conn = sqlite3.connect("ppt.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS puntajes (
        user_id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        puntos INTEGER DEFAULT 0
    )
""")
conn.commit()

# Forzar creación inmediata del archivo
c.execute("INSERT OR IGNORE INTO puntajes (user_id, nombre, puntos) VALUES (999, 'PRUEBA', 0)")
conn.commit()

def sumar_punto(user_id: int, nombre: str):
    c.execute("SELECT * FROM puntajes WHERE user_id = ?", (user_id,))
    if c.fetchone():
        c.execute("UPDATE puntajes SET puntos = puntos + 1, nombre = ? WHERE user_id = ?", (nombre, user_id))
    else:
        c.execute("INSERT INTO puntajes (user_id, nombre, puntos) VALUES (?, ?, 1)", (user_id, nombre))
    conn.commit()

def obtener_ranking():
    c.execute("SELECT nombre, puntos FROM puntajes ORDER BY puntos DESC")
    return c.fetchall()

# --- Botón de juego ---
async def comando_ppt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪨 Piedra", callback_data="ppt|piedra")],
        [InlineKeyboardButton("📄 Papel", callback_data="ppt|papel")],
        [InlineKeyboardButton("✂️ Tijera", callback_data="ppt|tijera")]
    ])
    await context.bot.send_message(
        chat_id=GRUPO_ID,
        message_thread_id=TEMA_ID,
        text="Elegí tu jugada:",
        reply_markup=teclado
    )

async def comando_rankingppt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = obtener_ranking()
    if not ranking:
        await update.message.reply_text("🎮 Aún no hay partidas registradas.")
        return

    texto = "🏆 Ranking Piedra, Papel o Tijera:\n\n"
    for i, (nombre, puntos) in enumerate(ranking, start=1):
        texto += f"{i}. {nombre} - {puntos} pts\n"
    await update.message.reply_text(texto)

async def comando_resetppt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c.execute("DELETE FROM puntajes")
    conn.commit()
    await update.message.reply_text("🔄 Ranking de Piedra, Papel o Tijera reiniciado.")

# --- Juego ---
async def jugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    eleccion_usuario = query.data.split("|")[1]
    eleccion_bot = random.choice(["piedra", "papel", "tijera"])

    if eleccion_usuario == eleccion_bot:
        resultado = "🤝 Empate"
    elif (eleccion_usuario == "piedra" and eleccion_bot == "tijera") or \
         (eleccion_usuario == "papel" and eleccion_bot == "piedra") or \
         (eleccion_usuario == "tijera" and eleccion_bot == "papel"):
        resultado = "🎉 Ganaste"
        sumar_punto(user.id, user.first_name)
    else:
        resultado = "😢 Perdiste"

    print(f"🪨📄✂️ {user.first_name} eligió {eleccion_usuario}, bot eligió {eleccion_bot} -> {resultado}")
    await query.edit_message_text(
        f"{user.first_name} eligió {eleccion_usuario}.\n"
        f"El bot eligió {eleccion_bot}.\n\n{resultado}"
    )

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("ppt", comando_ppt))
    app.add_handler(CommandHandler("rankingppt", comando_rankingppt))
    app.add_handler(CommandHandler("resetppt", comando_resetppt))
    app.add_handler(CallbackQueryHandler(jugar, pattern="^ppt\\|"))
    print("Bot PPT con SQLite activo.")
    app.run_polling()
