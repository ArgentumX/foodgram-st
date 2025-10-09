По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

## Docker setup

```bash
git clone https://github.com/ArgentumX/foodgram-st.git

# or

git clone git@github.com:ArgentumX/foodgram-st.git
```

```bash
cp ./backend/.env.Example.Docker ./backend/.env
```

```bash
docker compose up --build -d
```

```bash
docker compose exec backend python manage.py migrate
```

```bash
docker compose exec backend python manage.py createsuperuser
```

```bash
docker compose exec backend python manage.py loaddata ./data/ingredients_data.json
```

```bash
docker compose exec backend python manage.py loaddata ./data/test_data.json
```

```bash
docker compose exec backend python manage.py collectstatic --no-input
```
