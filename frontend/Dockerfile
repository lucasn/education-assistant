FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Expose Vite default port
EXPOSE 5173

# Start development server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
