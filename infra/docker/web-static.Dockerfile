FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c AS build
RUN npm install --global pnpm@10.34.5
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/api-contract/package.json ./packages/api-contract/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web ./apps/web
COPY packages/api-contract ./packages/api-contract
ENV VITE_DEMO_MODE=true
RUN pnpm --filter @petland/web build

FROM nginx:1.30.5-alpine@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
ARG REVISION=local
LABEL org.opencontainers.image.revision=$REVISION
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
COPY infra/docker/nginx.conf /etc/nginx/nginx.conf
COPY infra/docker/security-headers.conf /etc/nginx/security-headers.conf
EXPOSE 8443
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
