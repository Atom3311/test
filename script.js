const CONFIG = {
  SUPABASE_URL: "https://YOUR_SUPABASE_URL",
  SUPABASE_ANON_KEY: "YOUR_SUPABASE_ANON_KEY",
};

const useMock = CONFIG.SUPABASE_URL.includes("YOUR_") || CONFIG.SUPABASE_ANON_KEY.includes("YOUR_");
const STORAGE_KEY = "snowclicker:v1";

const ui = {
  coins: document.getElementById("coins"),
  cps: document.getElementById("cps"),
  streak: document.getElementById("streak"),
  multiplier: document.getElementById("multiplier"),
  level: document.getElementById("level"),
  collection: document.getElementById("collection"),
  clicker: document.getElementById("clicker"),
  ratingBody: document.querySelector("#rating tbody"),
  missionClicks: document.getElementById("mission-clicks"),
  missionCoins: document.getElementById("mission-coins"),
  missionBoosts: document.getElementById("mission-boosts"),
  toast: document.getElementById("toast"),
  userpic: document.getElementById("userpic"),
  username: document.getElementById("username"),
  userstatus: document.getElementById("userstatus"),
  profileName: document.getElementById("profile-name"),
  profileAvatar: document.getElementById("profile-avatar"),
  profileBadges: document.getElementById("profile-badges"),
  profileSeason: document.getElementById("profile-season"),
  profileAchievements: document.getElementById("profile-achievements"),
  profileBestMult: document.getElementById("profile-best-mult"),
  profileGifts: document.getElementById("profile-gifts"),
  payAmount: document.getElementById("pay-amount"),
  payBoost: document.getElementById("pay-boost"),
  payTotal: document.getElementById("pay-total"),
  payButton: document.getElementById("pay-button"),
  payMethods: document.getElementById("pay-methods"),
  snowstorm: document.getElementById("snowstorm"),
  carols: document.getElementById("carols"),
  gift: document.getElementById("gift"),
};

const state = {
  user: null,
  coins: 0,
  cps: 0,
  streak: 0,
  baseMult: 1,
  eventMult: 1,
  level: 1,
  collection: 0,
  clicks: 0,
  totalCoins: 0,
  boostsActivated: 0,
  bestMult: 1,
  gifts: 0,
  lucky: false,
  giftClaimed: false,
  boosts: { mult: 150, auto: 300, lucky: 500 },
};

const missions = {
  clicks: 50,
  coins: 1000,
  boosts: 3,
};

function showToast(message) {
  ui.toast.textContent = message;
  ui.toast.classList.add("show");
  setTimeout(() => ui.toast.classList.remove("show"), 1600);
}

function getCurrentMult() {
  return state.baseMult * state.eventMult;
}

function updateUI() {
  ui.coins.textContent = Math.floor(state.coins).toLocaleString("ru-RU");
  ui.cps.textContent = state.cps.toFixed(1);
  ui.streak.textContent = state.streak;
  ui.multiplier.textContent = `x${getCurrentMult().toFixed(1).replace(/\.0$/, "")}`;
  ui.level.textContent = state.level;
  ui.collection.textContent = `${state.collection}/12`;
  ui.profileBestMult.textContent = `x${state.bestMult}`;
  ui.profileGifts.textContent = String(state.gifts);
  updateMissions();
}

function updateMissions() {
  ui.missionClicks.textContent = `${Math.min(state.clicks, missions.clicks)}/${missions.clicks}`;
  ui.missionCoins.textContent = `${Math.min(Math.floor(state.totalCoins), missions.coins)}/${missions.coins}`;
  ui.missionBoosts.textContent = `${Math.min(state.boostsActivated, missions.boosts)}/${missions.boosts}`;
}

function gainCoins(amount, source) {
  const bonus = state.lucky && Math.random() < 0.08 ? 5 : 1;
  const added = amount * getCurrentMult() * bonus;
  state.coins += added;
  state.totalCoins += added;
  if (source === "click") state.clicks += 1;
  state.streak += 1;
  if (state.coins > state.level * 500) state.level += 1;
  state.bestMult = Math.max(state.bestMult, getCurrentMult());
  updateUI();
  persistProgress();
}

function openTab(name) {
  const tabs = document.querySelectorAll(".pill[data-tab]");
  const panels = {
    game: document.getElementById("tab-game"),
    rating: document.getElementById("tab-rating"),
    profile: document.getElementById("tab-profile"),
    win2pay: document.getElementById("tab-win2pay"),
  };

  Object.values(panels).forEach((panel) => panel.classList.add("hidden"));
  panels[name].classList.remove("hidden");
  tabs.forEach((t) => t.classList.remove("active"));
  tabs.forEach((t) => {
    if (t.dataset.tab === name) t.classList.add("active");
  });
}

function bindTabs() {
  document.querySelectorAll(".pill[data-tab]").forEach((tab) => {
    tab.addEventListener("click", () => openTab(tab.dataset.tab));
  });
  openTab("game");
}

function activateBoost(type) {
  const cost = state.boosts[type];
  if (state.coins < cost) {
    showToast("Не хватает монет");
    return;
  }
  state.coins -= cost;

  if (type === "mult") {
    state.baseMult = 2;
    setTimeout(() => {
      state.baseMult = 1;
      updateUI();
    }, 30000);
  }

  if (type === "auto") {
    state.cps += 5;
  }

  if (type === "lucky") {
    state.lucky = true;
    setTimeout(() => {
      state.lucky = false;
    }, 30000);
  }

  state.boostsActivated += 1;
  state.collection = Math.min(12, state.collection + 1);
  showToast("Буст активирован");
  updateUI();
  persistProgress();
}

function handlePaidBoost(btn) {
  const name = btn.querySelector("span").textContent;
  const price = btn.dataset.price;
  ui.payBoost.value = name;
  ui.payAmount.value = price;
  ui.payTotal.textContent = `₽ ${price}.00`;
  openTab("win2pay");
  showToast("Переход к оплате");
}

function bindBoosts() {
  document.querySelectorAll(".boost[data-boost]").forEach((btn) => {
    btn.addEventListener("click", () => activateBoost(btn.dataset.boost));
  });

  document.querySelectorAll(".paid-boost").forEach((btn) => {
    btn.addEventListener("click", () => handlePaidBoost(btn));
  });
}

function bindEvents() {
  ui.snowstorm.addEventListener("change", () => {
    document.body.classList.toggle("storm", ui.snowstorm.checked);
    showToast(ui.snowstorm.checked ? "Буря усилилась" : "Буря стихла");
  });

  ui.carols.addEventListener("change", () => {
    state.eventMult = ui.carols.checked ? 1.5 : 1;
    updateUI();
    showToast(ui.carols.checked ? "Колядки активны" : "Колядки выключены");
  });

  ui.gift.addEventListener("change", () => {
    if (ui.gift.checked && !state.giftClaimed) {
      state.giftClaimed = true;
      state.gifts += 1;
      gainCoins(120, "gift");
      showToast("Подарок получен");
    }
  });
}

function bindProfileActions() {
  document.getElementById("edit-profile").addEventListener("click", () => showToast("Редактор скоро"));
  document.getElementById("open-inventory").addEventListener("click", () => showToast("Инвентарь в разработке"));
  document.getElementById("link-account").addEventListener("click", () => showToast("Связка аккаунта скоро"));
}

function bindClaim() {
  document.getElementById("claim").addEventListener("click", () => {
    gainCoins(75, "claim");
    showToast("Подарочек активирован");
  });
}

function bindPay() {
  ui.payAmount.addEventListener("input", () => {
    const raw = ui.payAmount.value.replace(/[^0-9]/g, "");
    ui.payAmount.value = raw;
    ui.payTotal.textContent = raw ? `₽ ${raw}.00` : "₽ 0.00";
  });

  ui.payMethods.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      ui.payMethods.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  ui.payButton.addEventListener("click", () => {
    showToast("Оплата недоступна (заглушка)");
  });
}

function seedRating() {
  ui.ratingBody.innerHTML = "";
  const leagues = ["Север", "Полярная", "Ледяная", "Снежная"];
  for (let i = 1; i <= 100; i += 1) {
    const tr = document.createElement("tr");
    const coins = Math.floor(15000 - i * 97 + Math.random() * 500);
    tr.innerHTML = `
      <td>${i}</td>
      <td>Игрок_${String(i).padStart(3, "0")}</td>
      <td>${coins.toLocaleString("ru-RU")}</td>
      <td>${leagues[i % leagues.length]}</td>
    `;
    ui.ratingBody.appendChild(tr);
  }
}

function loadLocal() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveLocal(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function persistProgress() {
  if (!state.user) return;
  const payload = {
    user: state.user,
    progress: {
      coins: state.coins,
      cps: state.cps,
      streak: state.streak,
      baseMult: state.baseMult,
      eventMult: state.eventMult,
      level: state.level,
      collection: state.collection,
      clicks: state.clicks,
      totalCoins: state.totalCoins,
      boostsActivated: state.boostsActivated,
      bestMult: state.bestMult,
      gifts: state.gifts,
      lucky: state.lucky,
      giftClaimed: state.giftClaimed,
    },
  };

  if (useMock) {
    saveLocal(payload);
    return;
  }

  saveProgressToDb(payload);
}

async function saveProgressToDb(payload) {
  try {
    await fetch(`${CONFIG.SUPABASE_URL}/rest/v1/progress`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: CONFIG.SUPABASE_ANON_KEY,
        Authorization: `Bearer ${CONFIG.SUPABASE_ANON_KEY}`,
        Prefer: "resolution=merge-duplicates",
      },
      body: JSON.stringify({
        user_id: payload.user.id,
        data: payload.progress,
        updated_at: new Date().toISOString(),
      }),
    });
  } catch {
    showToast("Сохранение офлайн");
  }
}

async function fetchProfileFromDb(userId) {
  try {
    const resp = await fetch(`${CONFIG.SUPABASE_URL}/rest/v1/users?id=eq.${userId}&select=*`, {
      headers: {
        apikey: CONFIG.SUPABASE_ANON_KEY,
        Authorization: `Bearer ${CONFIG.SUPABASE_ANON_KEY}`,
      },
    });
    const data = await resp.json();
    return data[0] || null;
  } catch {
    return null;
  }
}

function hydrateProfile(profile) {
  ui.profileName.textContent = profile.display_name;
  ui.profileAvatar.textContent = profile.avatar || "❄";
  ui.profileSeason.textContent = profile.season;
  ui.profileAchievements.textContent = profile.achievements;
  ui.profileBadges.innerHTML = "";
  profile.badges.forEach((badge) => {
    const el = document.createElement("span");
    el.textContent = badge;
    ui.profileBadges.appendChild(el);
  });
}

function initTelegram() {
  const tg = window.Telegram ? window.Telegram.WebApp : null;
  if (!tg) {
    ui.userstatus.textContent = "Demo mode";
    return null;
  }
  tg.ready();
  tg.expand();
  tg.setHeaderColor("#0a0f2a");
  tg.setBackgroundColor("#0a0f2a");
  return tg;
}

async function initUser() {
  const tg = initTelegram();
  const tgUser = tg && tg.initDataUnsafe ? tg.initDataUnsafe.user : null;

  state.user = {
    id: tgUser ? String(tgUser.id) : "demo-1",
    username: tgUser?.username || "demo_user",
    display_name: tgUser?.first_name || "Гость",
    photo: tgUser?.photo_url || null,
  };

  ui.username.textContent = state.user.display_name;
  ui.userstatus.textContent = tg ? "Telegram" : "Demo";
  ui.userpic.textContent = state.user.display_name.slice(0, 2).toUpperCase();

  if (state.user.photo) {
    ui.userpic.style.backgroundImage = `url(${state.user.photo})`;
    ui.userpic.style.backgroundSize = "cover";
    ui.userpic.textContent = "";
  }

  let profile = null;
  let progress = null;

  if (useMock) {
    const local = loadLocal();
    if (local) {
      profile = local.user;
      progress = local.progress;
    }
  } else {
    profile = await fetchProfileFromDb(state.user.id);
  }

  const fallbackProfile = {
    display_name: state.user.display_name,
    avatar: "⛄",
    season: "Зима 2025",
    achievements: "0/30",
    badges: ["Ледяной", "Новичок"],
  };

  hydrateProfile(profile || fallbackProfile);

  if (progress) {
    Object.assign(state, progress);
  }

  updateUI();
}

function initSnow() {
  const snow = document.getElementById("snow");
  for (let i = 0; i < 50; i += 1) {
    const flake = document.createElement("div");
    flake.className = "flake";
    flake.style.left = `${Math.random() * 100}%`;
    flake.style.animationDelay = `${Math.random() * 10}s`;
    flake.style.animationDuration = `${8 + Math.random() * 8}s`;
    flake.style.opacity = `${0.4 + Math.random() * 0.6}`;
    flake.style.transform = `scale(${0.4 + Math.random() * 0.8})`;
    snow.appendChild(flake);
  }

  const style = document.createElement("style");
  style.textContent = `
    .flake {
      position: absolute;
      top: -10px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.8);
      box-shadow: 0 0 10px rgba(255, 255, 255, 0.6);
      animation: fall linear infinite;
    }
    .burst { animation: bump 0.3s ease; }
    @keyframes fall { to { transform: translateY(110vh); } }
    @keyframes bump { 50% { transform: scale(1.03) rotate(2deg); } }
  `;

  document.head.appendChild(style);
}

ui.clicker.addEventListener("click", () => {
  gainCoins(1, "click");
  ui.clicker.classList.remove("burst");
  void ui.clicker.offsetWidth;
  ui.clicker.classList.add("burst");
  if (window.Telegram && window.Telegram.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.impactOccurred("light");
  }
});

setInterval(() => {
  if (state.cps > 0) gainCoins(state.cps / 10, "auto");
}, 100);

bindTabs();
bindBoosts();
bindEvents();
bindProfileActions();
bindClaim();
bindPay();
seedRating();
initSnow();
initUser();
updateUI();



