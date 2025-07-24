# A web application built with Django for finding people inclined toward transhumanism.

## 🚀 Features

### 🔐 Authorization via Telegram
Secure sign-in via Telegram Bot with signature verification.

---

### 👤 Personal Account
Each user has a personal dashboard displaying their information.

![Personal account](demo/PersonalAccount.gif)

---

### ⚙️ Admin Panel
Full-featured Django admin interface.  
Create a superuser with:

```bash
python manage.py createsuperuser
```

 ![Admin panel](demo/AdminDemo.gif)

 ---

## How to run

### Cmd
```bash
git clone https://github.com/DreamyLunatic/MetaHomo_tgBot.git
cd MetaHomo_tgBot

python -m venv venv
source venv/bin/activate    # for Linux/macOS
OR
venv\Scripts\activate.bat   # for Windows

pip install -r requirements.txt
```

### Make settings inside .env
TELEGRAM_BOT_TOKEN='insert your bot token here (use BotFather for creation)'
DEBUG=True
...

### Make migrations
```bash
python manage.py migrate
python manage.py collectstatic
```

### Run!
```bash
python main.py
```

## Credits
Big thanks to:
- [Oleg](https://github.com/o5b) — for [repository](https://github.com/o5b/telegram-django-map). Tg - @o5b_dev
- Malvina Pushkova — for provided [map](https://www.google.com/maps/d/viewer?mid=10tOk78kyhG7wrDUweEBk34Uog-mElPIt&ll=54.792332677644666%2C40.635587836197296&z=5). Tg - @malvina_pushkova
