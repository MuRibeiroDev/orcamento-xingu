# --- Etapa 1: build do frontend ---
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# VITE_API_URL vazio -> a aplicação chama /api e /static de forma relativa (proxy do nginx).
RUN echo "VITE_API_URL=" > .env && npm run build

# --- Etapa 2: servir com nginx ---
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
