"""Offline tests: every collector's parse_* function against representative payloads."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.collectors import base, chrony, fortigate, ilo, pihole, plex, proxmox, snmp_switch, wazuh  # noqa: E402
from dashboard.config import load_config  # noqa: E402


def test_rate_tracker_computes_bits_per_second():
    rt = base.RateTracker()
    assert rt.update("k", 1000, now=0) is None
    assert rt.update("k", 1000 + 125_000, now=1) == pytest.approx(1_000_000)  # 125 kB/s = 1 Mbps
    assert rt.update("k", 5, now=2) is None  # counter wrap


def test_formatters():
    assert base.fmt_mbps(3_900_000) == "3.9 Mbps"
    assert base.fmt_mbps(50_000) == "50 Kbps"
    assert base.fmt_uptime(22 * 3600 + 5) == "0h 05m" or base.fmt_uptime(22 * 3600) == "22h 00m"
    assert base.fmt_uptime(86400 * 3 + 7200) == "3d 02h"
    assert base.fmt_int(16265) == "16,265"


def test_pihole_v6():
    s = pihole.parse_v6_summary({"queries": {"total": 16265, "blocked": 740, "percent_blocked": 4.55},
                                 "clients": {"active": 11, "total": 20}, "gravity": {"domains_being_blocked": 123}})
    assert s["total"] == 16265 and s["active_clients"] == 11 and s["gravity_domains"] == 123
    h = pihole.parse_v6_history({"history": [{"timestamp": 1, "total": 5}, {"timestamp": 2, "total": 7}]}, 24)
    assert h == [5.0, 7.0]


def test_pihole_v5():
    s = pihole.parse_v5_summary({"dns_queries_today": 10, "ads_blocked_today": 1, "ads_percentage_today": 10.0,
                                 "unique_clients": 3})
    assert s["total"] == 10 and s["active_clients"] == 3
    assert pihole.parse_v5_history({"domains_over_time": {"20": 2, "10": 1}}, 24) == [1.0, 2.0]


def test_wazuh_agents_and_alerts():
    agents = wazuh.parse_agents({"data": {"affected_items": [
        {"id": "000", "name": "manager", "status": "active"},
        {"id": "001", "name": "Aetherion", "status": "active"},
        {"id": "002", "name": "Argus", "status": "disconnected"}]}})
    assert [a["name"] for a in agents] == ["Aetherion", "Argus"]
    count, hist = wazuh.parse_alert_histogram({"hits": {"total": {"value": 4}},
                                               "aggregations": {"per_hour": {"buckets": [{"doc_count": 1}, {"doc_count": 3}]}}})
    assert count == 4 and hist == [1.0, 3.0]
    q = wazuh.alerts_query(12)
    assert q["query"]["bool"]["filter"][0]["range"]["rule.level"]["gte"] == 12


def test_chrony_parsing():
    t = chrony.parse_tracking("A29FC87B,162.159.200.123,3,1695324000.5,-0.000012345,0.00001,0.00002,-1.234,0.001,0.02,0.01,0.002,64.0,Normal\n")
    assert t["refid"] == "A29FC87B" and t["stratum"] == 3 and t["leap"] == "normal"
    assert chrony.fmt_offset(t["offset_s"]) == "-12 µs"
    src = chrony.parse_sources("^,*,time.cloudflare.com,3,6,377,45,-0.00001,0.00002,0.0001\n^,+,pool.ntp.org,2,6,377,40,0,0,0\n")
    assert src[0]["selected"] and src[0]["name"] == "time.cloudflare.com" and not src[1]["selected"]


def test_fortigate_parsing():
    cpu, mem = fortigate.parse_resource_usage({"results": {"cpu": [{"current": 3}], "mem": [{"current": 37}]}})
    assert (cpu, mem) == (3.0, 37.0)
    ifs = fortigate.parse_interfaces({"results": {"wan1": {"ip": "192.168.12.181 255.255.255.0", "link": True,
                                                            "rx_bytes": 10, "tx_bytes": 20}}})
    assert ifs["wan1"]["name"] == "wan1"
    vl = fortigate.parse_vlan_interfaces({"results": [{"name": "trusted", "type": "vlan", "vlanid": 20},
                                                       {"name": "wan1", "type": "physical"}]})
    assert vl == {20: "trusted"}
    leases = fortigate.count_leases_by_interface({"results": [{"interface": "trusted", "status": "leased"},
                                                               {"interface": "trusted", "status": "leased"},
                                                               {"interface": "iot", "status": "expired"}]})
    assert leases["trusted"] == 2 and leases["iot"] == 0
    aps = fortigate.parse_aps({"results": [{"name": "Basement AP", "status": "connected"}]})
    assert aps[0]["online"]


def test_snmp_name_normalisation():
    assert snmp_switch.norm("GigabitEthernet28") == "gi28" == snmp_switch.norm("gi 28")
    assert snmp_switch.norm("VLAN 20") == "vlan20"
    assert snmp_switch.port_number("gi12") == 12
    idx = snmp_switch.build_index({49: "gi1", 100: "vlan 20"}, {49: "GigabitEthernet1", 100: "VLAN 20"})
    assert idx["gi1"] == 49 and idx["vlan20"] == 100


def test_proxmox_resources():
    d = proxmox.parse_resources({"data": [
        {"type": "node", "node": "pve", "status": "online", "cpu": 0.12, "mem": 4e9, "maxmem": 16e9, "uptime": 90000},
        {"type": "qemu", "vmid": 100, "name": "athena", "status": "running", "node": "pve"},
        {"type": "lxc", "vmid": 101, "name": "argus", "status": "stopped", "node": "pve"},
        {"type": "storage", "storage": "local", "node": "pve", "disk": 50e9, "maxdisk": 100e9, "status": "available"}]})
    assert d["nodes"][0]["cpu"] == pytest.approx(12) and d["nodes"][0]["mem"] == pytest.approx(25)
    assert [g["name"] for g in d["guests"]] == ["athena", "argus"]
    assert d["storage"][0]["pct"] == pytest.approx(50)


def test_plex_sessions():
    s = plex.parse_sessions({"MediaContainer": {"size": 1, "Metadata": [
        {"title": "Pilot", "grandparentTitle": "Show", "User": {"title": "james"},
         "Player": {"state": "playing", "product": "Plex Web"}, "TranscodeSession": [{"videoDecision": "transcode"}]}]}})
    assert s[0]["title"] == "Show — Pilot" and s[0]["decision"] == "transcode"
    assert plex.parse_sections({"MediaContainer": {"Directory": [{"key": "1", "title": "Movies", "type": "movie"}]}})[0]["title"] == "Movies"


def test_ilo_parsing():
    sysinfo = ilo.parse_system({"PowerState": "On", "Status": {"Health": "OK"}, "Model": "ProLiant DL380",
                                "HostName": "phoenix", "Oem": {"Hp": {"PostState": "FinishedPost"}}})
    assert sysinfo["health"] == "OK" and sysinfo["post"] == "FinishedPost"
    th = ilo.parse_thermal({"Temperatures": [{"Name": "01-Inlet Ambient", "ReadingCelsius": 21},
                                             {"Name": "02-CPU 1", "ReadingCelsius": 40}],
                            "Fans": [{"FanName": "Fan 1", "CurrentReading": 18, "Units": "Percent"}]})
    assert th["cpu_c"] == 40 and th["inlet_c"] == 21 and th["fan_pct"] == 18
    assert ilo.parse_power({"PowerControl": [{"PowerConsumedWatts": 181}]}) == 181.0


def test_config_env_expansion(tmp_path):
    (tmp_path / ".env").write_text("SECRET=hunter2\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text("services:\n  - {id: a, type: link, url: 'http://x', password: '${SECRET}', other: '${MISSING:-dflt}'}\n")
    os.environ.pop("SECRET", None)
    c = load_config(cfg)
    assert c["services"][0]["password"] == "hunter2" and c["services"][0]["other"] == "dflt"
    assert c["dashboard"]["refresh_seconds"] == 30


def test_config_rejects_duplicate_ids(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("services:\n  - {id: a, type: link}\n  - {id: a, type: link}\n")
    with pytest.raises(ValueError):
        load_config(cfg)
