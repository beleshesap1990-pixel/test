# 🤖 Discord Community Bot

Hire/For-hire, reputation, deal onayı, moderasyon ve loglama özellikleri içeren kapsamlı bir Discord botu.

---

## 📋 Özellikler

| Özellik | Komut |
|---|---|
| Hiring post aç | `/hiring` |
| For-hire post aç | `/for-hire` |
| Staff onay kuyruğu | `/queue` |
| Kullanıcı profili | `/profile [@user]` |
| Vouch ver | `/vouch @user [yorum]` |
| Deal başlat | `/deal @satıcı [açıklama] [miktar]` |
| Sıralama | `/leaderboard` |
| Kullanıcı raporla | `/report @user [sebep]` |
| Uyarı ver | `/warn @user [sebep]` |
| Kick | `/kick @user [sebep]` |
| Ban | `/ban @user [sebep]` |
| Timeout | `/timeout @user [dakika]` |
| Audit logları | `/audit` |

---

## 🚀 Kurulum

### 1. Discord Bot Oluştur
1. [Discord Developer Portal](https://discord.com/developers/applications) → New Application
2. Bot sekmesi → Bot oluştur → Token kopyala
3. OAuth2 → URL Generator → `bot` + `applications.commands` seç
4. Bot Permissions: Administrator (veya ihtiyaç duyulanlar)
5. Oluşan URL ile botu sunucuna ekle

### 2. Yerel Kurulum
```bash
# Repoyu klonla veya dosyaları bir klasöre koy
cd discord-bot

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle ve TOKEN + ID'leri gir

# Gereksinimleri yükle
pip install -r requirements.txt

# Botu başlat
python main.py
```

---

## ☁️ Railway ile Ücretsiz Hosting

1. [railway.app](https://railway.app) → GitHub ile giriş yap
2. **New Project → Deploy from GitHub repo** seç
3. Bu klasörü bir GitHub reposuna push et
4. Railway'de repoyu seç
5. **Variables** sekmesine git → `.env.example` içindeki değişkenleri ekle
6. Deploy!

> ℹ️ Railway ücretsiz planda aylık ~500 saat veriyor. Bot 7/24 çalışırsa yaklaşık 21 gün yeter. Daha fazlası için $5/ay Hobby planı al.

---

## 📁 Dosya Yapısı

```
discord-bot/
├── main.py              # Bot başlatıcı
├── requirements.txt
├── railway.toml         # Railway config
├── .env.example         # Ortam değişkenleri şablonu
├── utils/
│   ├── database.py      # SQLite yöneticisi
│   └── logger.py        # Log gönderici
├── cogs/
│   ├── hiring.py        # Hiring/for-hire + onay kuyruğu
│   ├── reputation.py    # Vouch, deal, profil
│   ├── moderation.py    # Warn, kick, ban, timeout, rapor
│   ├── logging.py       # Otomatik event logları
│   └── profiles.py      # Leaderboard, audit
└── data/
    └── bot.db           # SQLite veritabanı (otomatik oluşur)
```

---

## ⚙️ Kanal ve Rol Ayarları

`.env` dosyasında şunları doldur:

| Değişken | Açıklama |
|---|---|
| `DISCORD_TOKEN` | Bot token'ın |
| `LOG_CHANNEL_ID` | Tüm logların gideceği kanal |
| `QUEUE_CHANNEL_ID` | Staff'ın post onaylayacağı kanal |
| `APPROVED_CHANNEL_ID` | Onaylı postların yayınlanacağı kanal |
| `REPORT_CHANNEL_ID` | Raporların gideceği kanal |
| `STAFF_ROLE_ID` | Staff rolü (moderasyon komutları için) |
