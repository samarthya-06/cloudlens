#!/bin/bash
# Run on the CloudLens EC2 host after unpacking the private deployment bundle.
set -euo pipefail
cd /srv/cloudlens/source
sudo dnf install -y docker unzip openssl
sudo systemctl enable --now docker
sudo mkdir -p /usr/local/lib/docker/cli-plugins
compose_tmp=$(mktemp)
buildx_tmp=$(mktemp)
trap 'rm -f "$compose_tmp" "$buildx_tmp"' EXIT
curl -fsSL https://github.com/docker/compose/releases/download/v5.6.0/docker-compose-linux-x86_64 -o "$compose_tmp"
printf '40343e21ca777173e69cff5dbafeb37c6f81f3b0d57d9e597f036e95eb63e76a  %s\n' "$compose_tmp" | sha256sum -c -
sudo install -m 755 "$compose_tmp" /usr/local/lib/docker/cli-plugins/docker-compose
sudo docker compose version
curl -fsSL https://github.com/docker/buildx/releases/download/v0.19.3/buildx-v0.19.3.linux-amd64 -o "$buildx_tmp"
printf '32ed111e941e385c2fb8261eba06a4056915718fd606f8278834ac1931d261a2  %s\n' "$buildx_tmp" | sha256sum -c -
sudo install -m 755 "$buildx_tmp" /usr/local/lib/docker/cli-plugins/docker-buildx
sudo docker buildx version
sudo mkdir -p /srv/cloudlens/runtime/index
sudo cp runtime/index/{index.npz,chunks.json,metadata.json} /srv/cloudlens/runtime/index/
sudo chown -R 10001:10001 /srv/cloudlens/runtime
compose_file=infra/compose.yaml
if [[ "${1:-}" == "--direct" ]]; then
  compose_file=infra/compose-direct.yaml
  sudo python3 infra/configure.py --direct
else
  sudo python3 infra/configure.py
fi
sudo docker compose -f "$compose_file" up -d --build
sudo docker compose -f "$compose_file" ps
