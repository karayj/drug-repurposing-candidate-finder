FROM node:20-alpine AS builder

WORKDIR /app

# Copy RAND PKI certificates and manually install them
COPY RAND_PKI_Root.pem /tmp/RAND_PKI_Root.pem
COPY RAND_PKI_Chain.pem /tmp/RAND_PKI_Chain.pem

# Manually add certificates to the existing CA bundle (Alpine has ca-certificates pre-installed in base image)
RUN cat /tmp/RAND_PKI_Root.pem >> /etc/ssl/certs/ca-certificates.crt && \
    cat /tmp/RAND_PKI_Chain.pem >> /etc/ssl/certs/ca-certificates.crt && \
    rm /tmp/RAND_PKI_Root.pem /tmp/RAND_PKI_Chain.pem

# Set certificate environment variables
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV npm_config_cafile=/etc/ssl/certs/ca-certificates.crt

# Now we can safely update packages
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

# Copy RAND PKI certificates and manually install them
COPY RAND_PKI_Root.pem /tmp/RAND_PKI_Root.pem
COPY RAND_PKI_Chain.pem /tmp/RAND_PKI_Chain.pem

# Manually add certificates to the existing CA bundle
RUN cat /tmp/RAND_PKI_Root.pem >> /etc/ssl/certs/ca-certificates.crt && \
    cat /tmp/RAND_PKI_Chain.pem >> /etc/ssl/certs/ca-certificates.crt && \
    rm /tmp/RAND_PKI_Root.pem /tmp/RAND_PKI_Chain.pem

# Set certificate environment variables
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Update packages
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

ENV NODE_ENV=production

# Copy built application
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/package.json ./package.json

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
