# pi-ultra-mcp Dockerfile
#
# Methodology pinning (§4.3):
#   - Node 20 (pi-mono engines.node >= 20.6.0)
#   - pi-coding-agent 0.70.6 (devDep, used by pi runtime when mounted)
#   - @modelcontextprotocol/sdk 1.29.0
#
# The Ultra binary is NOT baked in. Mount it at /opt/ultra/ultra at run time
# along with any config it needs (see launch.sh).
FROM node:20-slim

# Minimal tools: tini for clean signal handling, ca-certificates for TLS.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy manifests first for layer caching.
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Copy the rest of the project.
COPY tsconfig.json ./
COPY pi-ultra-mcp.ts ./
COPY smoke-test.sh ./
RUN chmod +x smoke-test.sh

# Install pi globally so `pi --no-builtin-tools -e ./pi-ultra-mcp.ts` works.
# pi is shipped as @mariozechner/pi-coding-agent and exposes the `pi` bin.
RUN npm install -g @mariozechner/pi-coding-agent@0.70.6

# Place where the host should mount the Ultra binary.
RUN mkdir -p /opt/ultra /workspace
ENV ULTRA_BIN=/opt/ultra/ultra
ENV PATH=/opt/ultra:${PATH}

WORKDIR /workspace

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["pi", "--no-builtin-tools", "-e", "/app/pi-ultra-mcp.ts"]
