FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Clear any cached build artifacts
RUN rm -rf dist node_modules/.vite node_modules/.cache

ARG VITE_API_URL=https://cf.rocktor.shop
ARG VITE_WS_URL=wss://cf.rocktor.shop/api/chat/ws
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
