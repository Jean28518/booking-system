# booking-system

## How to run in production

```bash
git clone https://github.com/Jean28518/booking-system.git
cd booking-system
docker-compose up -d

vim /etc/caddy/Caddyfile
booking.int.de {
  reverse_proxy localhost:10324
}

vim src/django/root/settings.py
DEBUG = False
ALLOWED_HOSTS = ["*"]
BASE_URL = "https://booking.int.de/
```

## How to develop

```bash
sudo apt-get install python3-venv python3-dev
cd src/django
python3 -m venv .env
```

Now you can run the `run_development.sh` file.
