#!/bin/sh
set -eu
mkdir -p /tmp/petland-tls
cp /run/certs/postgres.crt /tmp/petland-tls/server.crt
cp /run/certs/postgres.key /tmp/petland-tls/server.key
chown postgres:postgres /tmp/petland-tls/server.*
chmod 600 /tmp/petland-tls/server.key
exec docker-entrypoint.sh "$@"
