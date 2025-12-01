import asyncio
from telegram import Bot
import config

async def get_chat_id():
    print(f"🤖 Conectando com o token: {config.BOT_TOKEN[:10]}...")
    bot = Bot(token=config.BOT_TOKEN)
    
    try:
        # Pega as últimas atualizações que o bot recebeu
        updates = await bot.get_updates()
        
        if not updates:
            print("❌ Nenhuma mensagem encontrada. Certifique-se de ter enviado uma mensagem para o bot ou no grupo onde ele está.")
            return

        print("\n✅ Mensagens encontradas! Procure o seu grupo abaixo:\n")
        
        for update in updates:
            if update.message:
                chat = update.message.chat
                print(f"Tipo: {chat.type}")
                print(f"Nome: {chat.title or chat.username}")
                print(f"ID (COPIE ESTE NÚMERO): {chat.id}")
                print("-" * 30)
                
            elif update.channel_post:
                chat = update.channel_post.chat
                print(f"Tipo: {chat.type}")
                print(f"Nome: {chat.title}")
                print(f"ID (COPIE ESTE NÚMERO): {chat.id}")
                print("-" * 30)
                
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(get_chat_id())