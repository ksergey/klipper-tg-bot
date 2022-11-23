# kllipper-tg-bot
Telegram bot for Klipper

# Installation

Use the following command to enable automatic start-up of systemd user instances
```sh
sudo loginctl enable-linger ${USER}
```

Execute the following commands:

```sh
cd ~/
git clone https://github.com/ksergey/klipper-tg-bot.git
cd klipper-tg-bot
./scripts/install.sh
```

This script will install python packages, create a python virtual environment at `~/klipper-tg-bot-env` and install a
systemd service file under user.

To manual start or stop service execute the following command:
```sh
# start service
systemctl --user start klipper-tg-bot.service

# stop service
systemctl --user stop klipper-tg-bot.service

```

# Configuration

After installation you should configure the bot. By default config file placed in user home directory and has name
`klipper-tg-bot.conf`.

Configuration example:
```ini
[telegram]
# telegram bot api token from @BotFather (https://t.me/BotFather)
token = 270485614:AAHfiqksKZ8WmR2zSjiQ7_v4TMAKdiHm9T0
# telegram chat id where bot will talk and receive commands. It's could be telegram group or private chat with bot.
# @getmyid_bot (https://t.me/getmyid_bot) could help to obtain that number.
chat_id = 11111

[moonraker]
# address where moonraker service listen
endpoint = 127.0.0.1:7125

[webcam]
# url address of web camera to obtain single images (don't try action=stream)
# remove the section if you don't have web camera
url = http://127.0.0.1/webcam/?action=snapshot
```
