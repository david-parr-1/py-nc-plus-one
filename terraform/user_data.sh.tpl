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
sudo -u ubuntu git clone \
  --branch "${repo_branch}" \
  https://github.com/david-parr-1/py-nc-plus-one.git \
  "$TARGET_DIR"

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
EOF

echo "Adding FastAPI app service to systemd..." >> \
  /home/ubuntu/start-script-log.txt
sudo tee /etc/systemd/system/fastapi.service > /dev/null <<'EOF'
[Unit]
Description=FastAPI application
Wants=network-online.target
After=network-online.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/py-nc-plus-one
Environment=PYTHONPATH=/home/ubuntu/py-nc-plus-one
Environment=SSM_PARAMETER_PREFIX="${ssm_parameter_prefix}"
Environment=LOGGING_LEVEL="${logging_level}"
ExecStart=/home/ubuntu/py-nc-plus-one/.venv/bin/uvicorn \
  main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/fastapi.log
StandardError=append:/var/log/fastapi.log

[Install]
WantedBy=multi-user.target
EOF

echo "Installing CloudWatch agent" >> /home/ubuntu/start-script-log.txt
AGENT_URL="https://amazoncloudwatch-agent-${aws_region}.s3.${aws_region}"\
".amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb"
curl -fsSLo /tmp/amazon-cloudwatch-agent.deb "$AGENT_URL"
dpkg -i /tmp/amazon-cloudwatch-agent.deb

echo "Configuring CloudWatch agent" >> /home/ubuntu/start-script-log.txt
sudo install -d -m 0755 /opt/aws/amazon-cloudwatch-agent/etc

sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  >/dev/null <<EOF
{
  "agent": {
    "region": "${aws_region}",
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/fastapi.log",
            "log_group_name": "${cloudwatch_log_group_name}",
            "log_stream_name": "{instance_id}/fastapi",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

echo "Writing seed data to DB..." >> /home/ubuntu/start-script-log.txt
sudo -u ubuntu env \
  PYTHONPATH="$TARGET_DIR" \
  SSM_PARAMETER_PREFIX="${ssm_parameter_prefix}" \
  LOGGING_LEVEL="${logging_level}" \
  "$TARGET_DIR/.venv/bin/python" \
  "$TARGET_DIR/db/seed_database.py"

echo "Enabling and starting FastAPI service with systemd..." >> \
  /home/ubuntu/start-script-log.txt
sudo systemctl daemon-reload
sudo systemctl enable --now fastapi
