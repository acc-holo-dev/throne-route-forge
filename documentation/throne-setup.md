# Throne Setup

1. Push this repository to GitHub.
2. Run the `Build and Release` workflow or push to `main`.
3. Open the generated `latest` Release and copy `.srs` download links.
4. The bundled profiles already point to `acc-holo-dev/throne-route-forge`.
   Replace the owner only if you fork or move the repository.
5. Create a new Throne route profile for testing.
6. Add the proxy rule-set URLs first.
7. Add reject rule-sets only after confirming that the profile works.

Recommended rule order:

1. `reject-*`
2. `direct-*`
3. `proxy-*`
4. final/default route

The reject rule must be above proxy/direct rules, otherwise traffic may match a
route rule before it gets blocked.

Re-filter is connected as ready-made remote `.srs` rule-sets in the proxy rule:

```text
https://github.com/1andrevich/Re-filter-lists/releases/latest/download/ruleset-domain-refilter_domains.srs
https://github.com/1andrevich/Re-filter-lists/releases/latest/download/ruleset-ip-refilter_ipsum.srs
```
