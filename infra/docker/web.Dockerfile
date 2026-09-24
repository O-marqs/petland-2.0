FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c
RUN npm install --global pnpm@10.34.5
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/api-contract/package.json ./packages/api-contract/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web ./apps/web
COPY packages/api-contract ./packages/api-contract
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["pnpm", "--filter", "@petland/web", "exec", "vite", "--host", "0.0.0.0"]
