FROM node:20-alpine

WORKDIR /app

COPY web/package.json ./package.json
RUN npm install

COPY web ./
RUN npm run build

EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
