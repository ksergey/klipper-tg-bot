#!/bin/bash

echo "Uninstalling bot"
echo ""
echo "* Stopping service"
systemctl --user stop klipper-tg-bot.service
echo "* Removing unit file"
rm ${HOME}/.config/systemd/user/klipper-tg-bot.service
echo "* Removing enviroment"
rm -rf ${HOME}/klipper-tg-bot-env
echo "Done"
