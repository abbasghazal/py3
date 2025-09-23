# bot/config.py
import telebot
TOKEN = '7665348559:AAE-gaBCPLAkKV5s7BQPIQmZUxoOgaaBAGA'
DEVELOPER_ID = 6848908141
ADMINS = [DEVELOPER_ID]  # Admin user IDs
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
bot = telebot.TeleBot(TOKEN)