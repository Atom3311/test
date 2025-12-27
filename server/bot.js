import "dotenv/config";
import TelegramBot from "node-telegram-bot-api";

const TOKEN = process.env.TELEGRAM_BOT_TOKEN || "YOUR_TELEGRAM_BOT_TOKEN";
const SUPABASE_URL = process.env.SUPABASE_URL || "https://YOUR_SUPABASE_URL";
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "YOUR_SUPABASE_SERVICE_ROLE_KEY";
const WEBAPP_URL = process.env.WEBAPP_URL || "https://YOUR_WEBAPP_URL";

if (TOKEN.includes("YOUR_")) {
  console.warn("Set TELEGRAM_BOT_TOKEN before запуск");
}

const bot = new TelegramBot(TOKEN, { polling: true });

async function upsertUser(user) {
  if (SUPABASE_URL.includes("YOUR_")) return;
  const payload = {
    id: String(user.id),
    username: user.username || null,
    display_name: user.first_name || "Игрок",
    photo_url: user.photo_url || null,
    badges: ["Новичок"],
    season: "Зима 2025",
    achievements: "0/30",
  };

  await fetch(`${SUPABASE_URL}/rest/v1/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SUPABASE_SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      Prefer: "resolution=merge-duplicates",
    },
    body: JSON.stringify(payload),
  });
}

bot.onText(/\/(start|menu)/, async (msg) => {
  const chatId = msg.chat.id;
  if (msg.from) {
    try {
      await upsertUser(msg.from);
    } catch (err) {
      console.error("Supabase error", err.message);
    }
  }

  bot.sendMessage(chatId, "Открыть Снежный Кликер", {
    reply_markup: {
      inline_keyboard: [
        [{ text: "Открыть Mini App", web_app: { url: WEBAPP_URL } }],
      ],
    },
  });
});

bot.on("message", (msg) => {
  if (msg.text && msg.text.startsWith("/")) return;
  bot.sendMessage(msg.chat.id, "Нажми кнопку, чтобы открыть игру.");
});
