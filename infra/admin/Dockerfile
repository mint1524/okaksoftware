FROM node:20-alpine

WORKDIR /app

COPY admin/package.json ./package.json
RUN npm install

COPY admin ./
RUN npm run build

EXPOSE 4174
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4174"]
