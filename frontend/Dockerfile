FROM node:24-alpine

WORKDIR /app

# Install local dependencies
COPY package*.json ./
RUN npm install

# We use the host volume in development, but we install global angular cli just in case
RUN npm install -g @angular/cli@21

# Copy the rest of the files (useful if run without volume mapping)
COPY . .

EXPOSE 4200

# The startup command is overridden in docker-compose.yml for development
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]
