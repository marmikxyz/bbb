# Ranaji Stream 🎬

Telegram channel ke videos/PDFs ko apni website pe stream karo.

## System Architecture

```
Telegram Channel Post
        ↓
    Bot (bot.py)
        ↓ JSON file
    Owner ke Telegram pe aata hai
        ↓ Download karo
    /ranaji Admin Panel pe upload
        ↓
    Website pe video/PDF show hota hai
```

## Files

| File | Purpose |
|------|---------|
| `index.html` | Website + Admin Panel |
| `bot.py` | Telegram bot (local chalao) |
| `requirements.txt` | Bot dependencies |
| `vercel.json` | Vercel deploy config |

---

## STEP 1 — Website Deploy (Vercel)

1. GitHub pe new repo banao → in files upload karo
2. [vercel.com](https://vercel.com) → New Project → GitHub repo select karo
3. Deploy! (30 sec mein live)

**Admin Panel URL:** `https://yoursite.vercel.app/#ranaji`

---

## STEP 2 — Bot Setup (Local PC pe)

### Install karo:
```bash
pip install python-telegram-bot==20.7
```

### Bot ko channel mein add karo:
1. Apne Telegram channel mein bot ko **Admin** banao
2. Read Messages permission do kaafi hai

### Run karo:
```bash
python bot.py
```

### Bot ko start karo:
Telegram mein apne bot ko `/start` bhejo — Owner ID register hoga.

---

## STEP 3 — Flow

1. **Channel pe post karo** (video/PDF)
2. **Bot automatically** tumhare Telegram pe JSON file bhejega
3. JSON file **download** karo
4. Website ke **Admin Panel** (`#ranaji`) pe upload karo
5. **Save & Publish** dabao → Video website pe live! ✅

---

## Admin Panel Features

- 📂 Drag & drop JSON upload
- 📋 Sab posts ki list
- 🗑️ Delete posts
- ⬇️ Export all posts as JSON
- 💾 Save & Publish

## Video Player

- ✅ Small videos (<20MB): Direct CDN `<video>` player
- ⚠️ Large videos (>20MB): Telegram embed player
- 📄 PDFs: Google Docs viewer
- 🖼️ Photos: Direct image

---

## Bot Token

Already set in `bot.py`:
```
8783176299:AAHgfs_Kk2vpBRdLHQ4XLPcjGIvJmcjQQYw
```

> ⚠️ Is token ko public GitHub repo mein mat daalo!
> GitHub mein daalna ho toh `.env` file use karo aur `.gitignore` mein add karo.

---

## Security Tips

1. `.gitignore` mein add karo:
```
.env
```

2. `bot.py` mein token ko environment variable se lo:
```python
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
```
