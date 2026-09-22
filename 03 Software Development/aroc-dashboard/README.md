# AROC Dashboard

A single-pane status board for the KE4CON operations center: one page with a card
per device or service, each showing live data pulled from that thing's own API,
plus a button that opens its real management UI. No more remembering which IP
and port belongs to what.

**Part of Project AROC.** Licensed GPLv3 (see `LICENSING.md` at the repository
root). Nothing in this folder is specific to any one network: every host, port,
VLAN name and credential comes from `config.yaml`, which is never committed.

![demo layout](../../05%20Media/aroc-dashboard-demo.png)

## What it can talk to

| `type`        | Device / service            | How it gets data                                   |
|---------------|-----------------------------|----------------------------------------------------|
| `pihole`      | Pi-hole v6 (v5 fallback)    | REST API: queries, blocked %, clients, 24 h history |
| `wazuh`       | Wazuh manager (+ indexer)   | Manager API for agents; indexer for alerts/vulns    |
| `chrony`      | chrony time server          | `chronyc -c tracking/sources`, local or over SSH    |
| `fortigate`   | FortiGate (FortiOS 6/7)     | REST API: CPU/mem, WAN, DHCP, VLANs, Wi-Fi/APs      |
| `snmp_switch` | Cisco SG300 or any SNMP switch | IF-MIB / POWER-ETHERNET-MIB: uplink, PoE, per-VLAN traffic |
| `proxmox`     | Proxmox VE                  | API token: node CPU/RAM, VMs/LXCs, storage          |
| `plex`        | Plex Media Server           | X-Plex-Token: active streams, libraries             |
| `ilo`         | HP iLO 4/5/6 (any Redfish BMC) | Redfish: power, health, temps, fans, watts       |
| `link`        | anything else               | Just a button, optional HTTP reachability check     |

Adding another kind of device means adding one Python file under
`dashboard/collectors/` that returns a `Card`; the web page renders every card
the same way and needs no changes.

## Quick start

```bash
cd "03 Software Development/aroc-dashboard"
python3 -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# See the layout with fake data first:
python -m dashboard.demo                            # http://127.0.0.1:8080

# Then configure the real thing:
cp config.example.yaml config.yaml                  # edit: hosts, ports, VLAN names
cp .env.example .env                                # edit: tokens and passwords
AROC_HOST=100.64.0.5 python -m dashboard.main       # bind to your Tailscale IP
```

Open `http://<host>:8080/`. The page refreshes itself; click a card's header to
force an immediate re-poll of that one service.

### Where to get each credential

- **Pi-hole v6**: the web interface password (or an app password from
  *Settings → Web interface / API*). v5: *Settings → API → Show API token* and set
  `api_version: 5` with `api_token`.
- **Wazuh**: the API user (`wazuh-wui` by default) on port 55000. The indexer
  user is the OpenSearch `admin` (or a read-only user you create) on port 9200.
- **FortiGate**: *System → Administrators → Create New → REST API Admin*, profile
  `prof_admin` or a read-only profile, trusted host = the dashboard's IP.
- **Cisco SG300**: *Security → SNMP → Communities* (v2c) or *Users* (v3). Port
  names are matched loosely: `gi28`, `GigabitEthernet28` and `gi 28` all work.
- **Proxmox**: *Datacenter → Permissions → API Tokens*; give the token
  `PVEAuditor` on `/`. `token_id` is `user@realm!tokenname`.
- **Plex**: any request from a signed-in browser session carries `X-Plex-Token`
  in the URL, or use Plex's *Get Info → View XML* on any item.
- **HP iLO**: a read-only iLO user is enough for Redfish.
- **chrony**: nothing to configure on chrony itself. For `mode: ssh` the
  dashboard host needs an SSH key that can run `chronyc` on the time server.

### Security notes

- Credentials stay on the server. The browser only sees `/api/status`, which
  contains the rendered numbers, never tokens.
- Bind to a Tailscale or management-VLAN address (`AROC_HOST`). If you must expose
  it more widely, set `dashboard.auth` in `config.yaml` for HTTP basic auth and
  put it behind TLS (Caddy, nginx, or Tailscale Serve).
- `verify_tls: false` is per service and only for self-signed management
  interfaces on your own LAN.
- The FortiGate card's "Public IP" is looked up from `api.ipify.org` because on a
  double-NAT link the FortiGate only knows its ISP-gateway-side WAN address. Set
  `public_ip_url: null` to disable the lookup.

## Running it permanently

- **Docker**: `docker compose up -d` (see `docker-compose.yml`; mount your
  `config.yaml` and `.env`).
- **systemd**: copy `aroc-dashboard.service` to `/etc/systemd/system/`, adjust
  paths, `systemctl enable --now aroc-dashboard`.

## API

| Endpoint                         | Purpose                                   |
|----------------------------------|-------------------------------------------|
| `GET /api/status`                | Every card, plus page title and refresh   |
| `GET /api/services/{id}`         | One card                                  |
| `POST /api/services/{id}/refresh`| Poll one service now                      |
| `GET /api/types`                 | Collector types this build knows          |
| `GET /healthz`                   | Liveness                                  |

The card model is documented at the top of `dashboard/collectors/base.py`.

## Tests

```bash
pip install pytest
python -m pytest tests
```

The tests exercise every collector's parsing against representative API
payloads, so they run with no devices on the network.

## Layout

```
dashboard/
  main.py              FastAPI app, background poll loop, JSON API
  config.py            config.yaml + .env loading
  demo.py              fake-data preview server
  collectors/          one module per device type (see table above)
  static/              index.html, style.css, app.js (no build step, no framework)
tests/                 offline parser tests
config.example.yaml    annotated template — copy to config.yaml
.env.example           secrets template — copy to .env
```
