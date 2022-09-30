# Телеграм-бот для отслеживания статуса домашних работ
Оповещает о смене статуса домашней работы, загруженной на Яндекс.Практикум.

## Описание
Бот делает запрос к API Практикум.Домашка, и если от сервиса вернулся ответ, содержащий домашнюю работу с новым статусом,
то бот отправляет сообщение об изменении статуса в чат с переданным id.

## Технологии

    Python 3.7.9
    requests==2.26.0
    flake8==3.9.2
    flake8-docstrings==1.6.0
    pytest==6.2.5
    python-dotenv==0.19.0
    python-telegram-bot==13.7

## Как запустить проект
```
git clone https://github.com/BU-Marina/homework_bot
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

Если у вас linux/MacOS:

```
. venv/bin/activate
```

Если у вас Windows:

```
. venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Добавить токен своего бота в переменные окружения через .env:

```
mv .env.example .env
nano .env
```

Вставить токен, полученный в Я.Практикуме ([по ссылке](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a)), затем токен своего бота и чата, куда будут приходить оповещения.
Сохранить изменения и выйти из режима (ctrl+o -> Enter -> ctrl+x)

---
Запустить проект:

```
python homework_bot.py
```

