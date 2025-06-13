# booking-system

## How to run in production

```bash
git clone https://github.com/Jean28518/booking-system.git
cd booking-system
vim docker-compose.yml
# Change here the environment variables to your needs
docker-compose up -d
# The first startup needs about 2 to 5 minutes.

# Insert the following lines into your Caddyfile (if you use Caddy as reverse proxy)
vim /etc/caddy/Caddyfile
booking.int.de {
  reverse_proxy localhost:10324
}
```

### How to reset the password for a user

```bash
docker exec -it booking-system_django_gunicorn_1 bash -l
cd /app
python manage.py changepassword myuser
```



## How to develop

```bash
sudo apt-get install python3-venv python3-dev

sudo -i
# Install languages
if ! grep -q "de_DE.UTF-8 UTF-8" /etc/locale.gen; then
    echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen
fi
sed -i 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen
if ! grep -q "en_GB.UTF-8 UTF-8" /etc/locale.gen; then
  echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen
fi
sed -i 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen
locale-gen
exit

# How to generate the .po files for translation
bash generate_po_files.sh


cd src/django
python3 -m venv .venv
```

Now you can run the `run_development.sh` file.
