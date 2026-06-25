# Throne Setup

1. Push this repository to GitHub.
2. Run the `Build and Release` workflow or push to `main`.
3. Open the generated `latest` Release and copy `.srs` download links.
4. Replace `YOUR_USERNAME` in `route-profiles/throne/*.json`.
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
