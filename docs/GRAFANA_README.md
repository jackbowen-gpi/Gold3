# Grafana

Grafana visualizes Prometheus metrics and other datasources. This repo includes a Grafana compose service with provisioning for a Prometheus datasource and a simple dashboard.

## Service name
- `grafana` in `docker-compose.yml`.

## Access
- UI: http://127.0.0.1:3000 (default admin user created on first start; password is set by compose to `grafana` in this repo).

## Provisioning
- `grafana/provisioning/datasources/datasources.yml` — adds Prometheus datasource pointing at `http://prometheus:9090`.
- `grafana/provisioning/dashboards/dashboards.yml` — auto-loads dashboards in the dashboards folder.

## Troubleshooting
- If dashboards don't load: check provisioning logs in Grafana and ensure the `prometheus` service is available.

## Links
- Grafana docs: https://grafana.com/docs/
