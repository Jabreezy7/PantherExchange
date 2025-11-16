FROM node:alpine

# Set the working directory to be /app
WORKDIR /app

# Copy dependency files first for caching
COPY package.json package-lock.json ./

# Install dependencies from package.json
RUN npm install

# Copy all frontend files from /PantherExchange into /app
COPY . .

# Expose the port Vite uses
EXPOSE 3000

# Run the Development server
CMD ["npm", "run", "dev", "--", "--host"]
