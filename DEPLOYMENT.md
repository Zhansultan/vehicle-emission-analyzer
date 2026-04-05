# Deployment Guide - Vehicle Emission Analyzer

## Option 1: Railway (Recommended - Easiest)

Railway автоматически деплоит из GitHub и поддерживает PostgreSQL.

### Шаг 1: Подготовка репозитория

```bash
# Инициализируй git если еще не сделал
git init
git add .
git commit -m "Initial commit with geolocation and frontend"

# Создай репозиторий на GitHub и запушь
git remote add origin https://github.com/YOUR_USERNAME/vehicle-emission-analyzer.git
git branch -M main
git push -u origin main
```

### Шаг 2: Настройка Railway

1. Зайди на https://railway.app и войди через GitHub
2. Нажми **"New Project"** → **"Deploy from GitHub repo"**
3. Выбери свой репозиторий

### Шаг 3: Добавь PostgreSQL

1. В проекте нажми **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway автоматически создаст `DATABASE_URL`

### Шаг 4: Настрой Backend сервис

1. Нажми на backend сервис → **Settings**
2. **Root Directory:** `/` (корень)
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. Добавь **Variables:**
   ```
   DATABASE_URL = ${{Postgres.DATABASE_URL}}
   PYTHONUNBUFFERED = 1
   ```

### Шаг 5: Настрой Frontend сервис

1. **"+ New"** → **"GitHub Repo"** (тот же репо)
2. **Root Directory:** `frontend`
3. **Build Command:** `npm install && npm run build`
4. **Start Command:** `npm run preview -- --host --port $PORT`

5. Добавь **Variables:**
   ```
   VITE_API_URL = https://your-backend-url.railway.app
   ```

---

## Option 2: Render (Free Tier Available)

### Шаг 1: Создай render.yaml в корне проекта

```yaml
# render.yaml
services:
  # Backend
  - type: web
    name: emission-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: emission-db
          property: connectionString
      - key: PYTHON_VERSION
        value: "3.11"

  # Frontend
  - type: web
    name: emission-frontend
    runtime: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://emission-api.onrender.com

databases:
  - name: emission-db
    plan: free
```

### Шаг 2: Деплой на Render

1. Зайди на https://render.com
2. **New** → **Blueprint** → Подключи GitHub репо
3. Render прочитает `render.yaml` и создаст все сервисы

---

## Option 3: VPS с Docker (DigitalOcean/Linode)

Для полного контроля - арендуй VPS и используй docker-compose.

### Шаг 1: Создай Droplet на DigitalOcean

1. Зайди на https://digitalocean.com
2. Create Droplet → **Docker on Ubuntu** (Marketplace)
3. Выбери план: $6/месяц минимум (лучше $12 для ML)
4. Добавь SSH ключ

### Шаг 2: Настрой сервер

```bash
# Подключись к серверу
ssh root@YOUR_SERVER_IP

# Клонируй репозиторий
git clone https://github.com/YOUR_USERNAME/vehicle-emission-analyzer.git
cd vehicle-emission-analyzer

# Создай .env для продакшена
cat > .env << EOF
DATABASE_URL=postgres://postgres:postgres@db:5432/emissions
DEBUG=false
EOF

# Создай .env для фронтенда
cat > frontend/.env << EOF
VITE_API_URL=http://YOUR_SERVER_IP:8000
EOF
```

### Шаг 3: Обнови docker-compose для продакшена

```bash
# Запусти все сервисы
docker-compose up -d --build

# Проверь логи
docker-compose logs -f
```

### Шаг 4: Настрой Nginx (опционально, для домена)

```bash
apt install nginx certbot python3-certbot-nginx

# Создай конфиг
cat > /etc/nginx/sites-available/emission << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/emission /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL сертификат (бесплатный)
certbot --nginx -d your-domain.com
```

---

## Важные изменения для продакшена

### 1. Обнови Dockerfile для фронтенда

Создай `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. Создай frontend/nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Обнови docker-compose.prod.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: emissions
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-strongpassword123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  app:
    build: .
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD:-strongpassword123}@db:5432/emissions
    depends_on:
      - db
    restart: always

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: ${API_URL:-http://localhost:8000}
    ports:
      - "80:80"
    depends_on:
      - app
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - app
      - frontend
    restart: always

volumes:
  postgres_data:
```

---

## Быстрый старт (Railway)

Самый быстрый способ - Railway:

```bash
# 1. Установи Railway CLI
npm install -g @railway/cli

# 2. Залогинься
railway login

# 3. Инициализируй проект
railway init

# 4. Добавь PostgreSQL
railway add --plugin postgresql

# 5. Задеплой
railway up

# 6. Открой в браузере
railway open
```

---

## Стоимость хостинга

| Платформа | Бесплатно | Платно |
|-----------|-----------|--------|
| Railway | $5 кредитов/месяц | от $5/месяц |
| Render | Free tier (спит после 15 мин) | от $7/месяц |
| DigitalOcean | - | от $6/месяц (VPS) |
| Fly.io | Free tier | от $5/месяц |

**Рекомендация:** Начни с Railway - самый простой деплой для твоего стека.
