#!/usr/bin/env bash
# Развёртывание SunnyFl_bot на свежем Ubuntu 24.04 (Hetzner Cloud).
# Запускать на сервере под root:  bash deploy_hetzner.sh
set -euo pipefail

APP_USER="bot"
APP_DIR="/home/${APP_USER}/tg_bot"
SERVICE="/etc/systemd/system/tgbot.service"

echo "==> Обновление системы и установка пакетов"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git ca-certificates tzdata

echo "==> Пользователь ${APP_USER}"
id -u "${APP_USER}" >/dev/null 2>&1 || adduser --disabled-password --gecos "" "${APP_USER}"

echo "==> Папка приложения ${APP_DIR}"
mkdir -p "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "/home/${APP_USER}"

if [ ! -f "${APP_DIR}/bot.py" ]; then
  echo "ERROR: файлы бота не найдены в ${APP_DIR}."
  echo "Сначала залей файлы через scp (см. инструкцию), потом запусти скрипт снова."
  exit 1
fi

if [ ! -f "${APP_DIR}/.env" ]; then
  echo "ERROR: ${APP_DIR}/.env отсутствует."
  echo "Создай .env с TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, ANTHROPIC_API_KEY."
  exit 1
fi

echo "==> Виртуальное окружение Python"
sudo -u "${APP_USER}" bash -lc "
  cd '${APP_DIR}'
  python3 -m venv venv
  ./venv/bin/pip install --upgrade pip
  ./venv/bin/pip install -r requirements.txt
"

echo "==> systemd unit ${SERVICE}"
cat > "${SERVICE}" <<EOF
[Unit]
Description=SunnyFl Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"

systemctl daemon-reload
systemctl enable tgbot
systemctl restart tgbot
sleep 2
systemctl --no-pager status tgbot | head -n 20 || true

echo ""
echo "==> Готово. Логи:  journalctl -u tgbot -f"
