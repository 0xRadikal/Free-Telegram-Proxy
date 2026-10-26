# Security

## Reporting
Please report vulnerabilities privately via GitHub → Security → *Report a vulnerability*. Do not open a public issue.

## What this project does and does not do
- It **publishes third-party proxies** it did not run. A proxy operator can see your IP address and connection times. Telegram traffic itself stays encrypted end-to-end by MTProto; the proxy cannot read messages.
- The pipeline makes outbound connections only: HTTP(S) to the listed sources and DB-IP, and MTProto probes to proxies. Private/reserved IPs (RFC1918, loopback, link-local, CGNAT…) are never probed.
- Workflows use the built-in `GITHUB_TOKEN` (`contents: write` only for the publish job, `read` elsewhere). Actions are pinned to full commit SHAs; Dependabot proposes updates.
- The optional server trigger (`tools/server`) only sends `repository_dispatch`; its token is read from a root-only file and never passed on a command line.
