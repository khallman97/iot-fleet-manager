FROM node:18-alpine

WORKDIR /app

# Install dependencies first for caching
COPY package.json package-lock.json* ./ 
RUN npm install

# Copy everything else
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
