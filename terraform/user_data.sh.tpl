#!/bin/bash

exec > /home/ubuntu/start-script-log.txt 2>&1

echo "Starting user_data script" >> /home/ubuntu/start-script-log.txt
export DEBIAN_FRONTEND=noninteractive

echo "Doing system updates and upgrades" >> /home/ubuntu/start-script-log.txt
apt-get update -y
apt-get upgrade -y

echo "Installing Python, pip, venv" >> /home/ubuntu/start-script-log.txt
apt-get install python3 python3-pip python3-venv -y

TARGET_DIR="/home/ubuntu/py-nc-plus-one"

echo "Clone Git repository started..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu git clone https://github.com/david-parr-1/py-nc-plus-one.git "$TARGET_DIR"

echo "Changing to repo directory..." >> /home/ubuntu/start-script-log.txt
cd "$TARGET_DIR"

echo "Creating venv..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu python3 -m venv .venv

echo "Installing dependencies..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu .venv/bin/pip install --upgrade pip
sudo -u ubuntu .venv/bin/pip install -r requirements.txt

echo "Creating .env file..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu tee .env <<EOF
PYTHONPATH="/home/ubuntu/py-nc-plus-one"
DB_NAME="${db_name}"
DB_USERNAME="${db_username}"
DB_PASSWORD="${db_password}"
DB_HOST="${db_host}"
DB_PORT="${db_port}"
JWT_EXPIRY_MINUTES="${jwt_expiry_minutes}"
JWT_ALGORITHM="${jwt_algorithm}"
JWT_SECRET="${jwt_secret}"
EOF

echo "Starting FastAPI server..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > fastapi
