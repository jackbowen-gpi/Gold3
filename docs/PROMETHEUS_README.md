# Prometheus

Prometheus is used to scrape metrics exposed by services (Flower, node_exporter, etc.) and store them for querying by Grafana.

## Purpose in this repo
- Scrapes `/metrics` endpoints for Flower and node_exporter and stores time-series metrics.

## Config file
- `prometheus/prometheus.yml` — the scrape config used in the compose setup.

## Running
```pwsh
docker-compose -f ../../config/docker-compose.yml up -d prometheus
docker-compose -f ../../config/docker-compose.yml logs -f prometheus
```

## Verify targets
- Open Prometheus UI: http://127.0.0.1:9090/targets to see scrape targets and status.

## Useful queries
- up — which targets are up: `up`
- scrape duration: `scrape_duration_seconds`

## Troubleshooting
- Target down due to missing exporter: check the compose service is running and exposed on the network.
- If scraping host-level metrics (cadvisor) fails on Windows/WSL, remove cadvisor target (was removed earlier in this repo due to host mount errors).

## Links
- Prometheus docs: https://prometheus.io/docs/introduction/overview/
