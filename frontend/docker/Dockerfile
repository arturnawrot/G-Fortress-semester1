# ========== Base for Node tasks ==========
FROM node:22-alpine AS base
WORKDIR /app

RUN apk add --no-cache git bash tini
RUN corepack enable || true
ENV CI=true

RUN git config --global user.name "Your Username"
RUN git config --global user.email youremail@example.com

# ========== Dev stage (runs in compose `node` service) ==========
FROM base AS dev
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
RUN mkdir -p /app/node_modules && chown -R node:node /app
USER node
EXPOSE 5173

# ========== Builder (production) ==========
FROM base AS build
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
RUN npm run build

# ========== Nginx runtime (production) ==========
FROM nginx:1.29-alpine AS nginx
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build/client /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]