import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN: str = os.environ["TG_BOT_TOKEN"]

# Владелец — куда слать уведомления о новых диалогах
OWNER_CHAT_ID: str = os.environ["TG_OWNER_CHAT_ID"]

# Claude API
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Supabase (опционально — для хранения истории)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

# Имя ассистента — как он представляется клиентам
ASSISTANT_NAME: str = os.getenv("ASSISTANT_NAME", "Помощник")

# Имя владельца (консультанта)
OWNER_NAME: str = os.getenv("OWNER_NAME", "Вусал")
