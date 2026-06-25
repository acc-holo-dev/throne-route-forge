# Source Policy

Prefer raw text files from public repositories:

```text
https://raw.githubusercontent.com/owner/repo/main/list.txt
```

Use `rule-lists/external-includes.json` for sources that should be added to a
target rule-set. Use `rule-lists/external-excludes.json` for sources that should
be removed from a target rule-set after local and external includes are merged.

Good sources are:

- Plain domain lists.
- Plain IP/CIDR lists.
- Stable URLs with clear license.
- Sources that are updated regularly.

Avoid:

- Personal subscription URLs.
- Links with tokens.
- Lists with unclear format.
- Lists that mix domains, IPs, comments, and app-specific syntax heavily.

If a source is unstable, keep it disabled until reviewed:

```json
{
  "name": "review-before-use",
  "enabled": false,
  "type": "domain",
  "target": "proxy/domains",
  "url": "https://raw.githubusercontent.com/owner/repo/main/list.txt"
}
```
