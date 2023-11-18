#!/bin/bash

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$( cd "${SCRIPT_PATH}/.." >/dev/null 2>&1; pwd -P )"
ENV_PATH="${HOME}/klipper-tg-bot-env"

Red='\033[0;31m'
Green='\033[0;32m'
Cyan='\033[0;36m'
Normal='\033[0m'

echo_text()
{
  printf "${Normal}$1${Cyan}\n"
}

echo_error()
{
  printf "${Red}$1${Normal}\n"
}

echo_ok()
{
  printf "${Green}$1${Normal}\n"
}

create_virtualenv()
{
  echo_text "Creating virtual environment"
  if [ ! -d "${ENV_PATH}" ]; then
    virtualenv -p /usr/bin/python3 --system-site-packages "${ENV_PATH}"
  fi

  source "${ENV_PATH}/bin/activate"

  while read requirements; do
    python3 -m pip --disable-pip-version-check --no-cache-dir install $requirements
    if [ $? -gt 0 ]; then
    	echo "Error: pip install exited with status code $?"
      echo "Unable to install dependencies, aborting install."
      deactivate
      exit 1
    fi
  done < ${ROOT_PATH}/requirements.txt
  deactivate
  echo_ok "Virtual enviroment created"
}

create_default_config()
{
  echo_text "Create default config"
  if [ ! -f "${HOME}/klipper-tg-bot.conf" ]; then
    cp "${ROOT_PATH}/klipper-tg-bot.conf" "${HOME}/klipper-tg-bot.conf"
    echo "Default config created (${HOME}/klipper-tg-bot.conf)"
  else
    echo "Config already exists (${HOME}/klipper-tg-bot.conf)"
  fi
}

install_systemd_service()
{
  echo_text "Installing systemd unit file"

  mkdir -p ${HOME}/.config/systemd/user

cat > ${HOME}/.config/systemd/user/klipper-tg-bot.service <<EOF
[Unit]
Description=Telegram bot for Klipper
After=network.target

[Service]
Type=simple
WorkingDirectory=${ROOT_PATH}
ExecStart=${ENV_PATH}/bin/python3 -m app --config ${HOME}/klipper-tg-bot.conf
Restart=always
RestartSec=15
KillSignal=SIGINT

[Install]
WantedBy=default.target
EOF

  systemctl --user unmask klipper-tg-bot.service
  systemctl --user daemon-reload
  systemctl --user enable klipper-tg-bot.service
}

create_virtualenv
create_default_config
install_systemd_service

echo_ok "Klipper telegram bot was installed"
echo_ok "Now edit ${HOME}/klipper-tg-bot.conf and start bot service"
echo_ok "   systemctl --user start klipper-tg-bot.service"
