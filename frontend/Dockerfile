FROM node:20-slim
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
CMD ["sh", "-c", "serve -s dist -l $PORT"]
