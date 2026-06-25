# Throne Route Forge

Source-driven route-set builder for Throne and sing-box.

The repository keeps readable local rules, imports external include and exclude
lists, builds sing-box rule-set JSON, compiles `.srs` assets in GitHub Actions,
and publishes ready-to-use release files for Throne.

## Layout

```text
rule-lists/
  external-includes.json      external lists added to rule-sets
  external-excludes.json      external lists removed from rule-sets
  local-rules/                your own rules
    proxy/domains.txt
    proxy/ip-cidrs.txt
    direct/domains.txt
    direct/ip-cidrs.txt
    reject/domains.txt
    reject/ip-cidrs.txt
  excluded-rules/             local rules removed after merge
    proxy/domains.txt
    proxy/ip-cidrs.txt
    direct/domains.txt
    direct/ip-cidrs.txt
    reject/domains.txt
    reject/ip-cidrs.txt

route-profiles/
  throne/                     Throne route profile examples
  sing-box/                   sing-box snippets

source/throne_route_forge/    build and validation scripts
release-assets/               generated release assets
documentation/                setup and source notes
```

## Release Assets

- `proxy-domains.srs`
- `proxy-ips.srs`
- `direct-domains.srs`
- `direct-ips.srs`
- `reject-domains.srs`
- `reject-ips.srs`
- `route-profile-throne-minimal.json`
- `route-profile-throne-full.json`
- `sing-box-route-snippet.json`
- `sing-box-rule-sets-snippet.json`
- `checksums.txt`

## Throne Links

After the first successful GitHub Actions run, use release links like these:

```text
https://github.com/YOUR_USERNAME/throne-route-forge/releases/latest/download/proxy-domains.srs
https://github.com/YOUR_USERNAME/throne-route-forge/releases/latest/download/proxy-ips.srs
https://github.com/YOUR_USERNAME/throne-route-forge/releases/latest/download/reject-domains.srs
```

Replace `YOUR_USERNAME` with your GitHub username or organization.

## Local Rules

Add one item per line to the matching file in `rule-lists/local-rules/`.

Domain files support:

```text
example.com
domain:example.org
suffix:example.net
keyword:discord
regexp:^.+\.example\.com$
```

IP/CIDR files support:

```text
1.1.1.1
8.8.8.0/24
2001:4860:4860::8888/128
```

Lines starting with `#` are comments.

## External Includes And Excludes

Use `rule-lists/external-includes.json` to import lists into a target rule-set.
Use `rule-lists/external-excludes.json` to import lists that must be removed
from a target rule-set.

Example:

```json
{
  "name": "external-proxy-domains",
  "enabled": true,
  "type": "domain",
  "target": "proxy/domains",
  "url": "https://raw.githubusercontent.com/owner/repo/main/domains.txt"
}
```

Targets are:

- `proxy/domains`
- `proxy/ips`
- `direct/domains`
- `direct/ips`
- `reject/domains`
- `reject/ips`

## Reject Means Block

`reject` is local blocking. If a connection matches a reject rule, the client
refuses or drops it instead of sending it direct or through VPN. Keep reject
rules above direct/proxy rules in route profiles.

## Safety

Do not commit VPN subscription links, UUIDs, private keys, access tokens, proxy
server configs, or personal URLs with private query parameters.

## Local Build

Python 3.11+ is enough for JSON generation:

```powershell
python source/throne_route_forge/build_rule_sets.py --strict
python source/throne_route_forge/validate_rule_sets.py
```

GitHub Actions also downloads `sing-box`, compiles `.srs`, copies profile
assets, writes checksums, and publishes the latest release.
