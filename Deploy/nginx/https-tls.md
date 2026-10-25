# Day 13 — HTTPS, Reverse Proxy & TLS

## Objective

Configure Nginx as a reverse proxy for the existing FastAPI application and enable HTTPS for local testing.

## Architecture

Client → Nginx (port 443) → FastAPI (port 3002) → vLLM (port 8000)

## Environment

- Local environment: WSL Ubuntu
- FastAPI port: 3002
- vLLM port: 8000
- Nginx: ports 80 and 443
- Certificate: self-signed, for localhost

## Files

- `deploy/nginx/llm-api.conf`: Nginx source configuration
- `/etc/nginx/sites-available/llm-api`: installed Nginx configuration
- `/etc/nginx/ssl/localhost.crt`: local TLS certificate
- `/etc/nginx/ssl/localhost.key`: TLS private key

The private key is not stored in Git.

## Commands

Validate Nginx:

```bash
sudo nginx -t
```

Reload Nginx:

```bash
sudo service nginx reload
```

Test HTTPS:

```bash
curl -k -i https://localhost/
```

Test HTTP redirection:

```bash
curl -I http://localhost/
```

## Key learnings

1. HTTPS uses TLS to encrypt HTTP traffic.
2. Nginx can terminate TLS and forward requests to FastAPI.
3. A reverse proxy separates the public entry point from the application backend.
4. HTTP can be redirected to HTTPS.
5. Self-signed certificates are suitable for local practice but are not automatically trusted by browsers.
6. The Nginx source configuration is version-controlled; its installed copy lives under `/etc/nginx/`.

## Limitations

This is a local learning setup. A publicly trusted certificate and suitable network configuration are needed for a production API exposed to the internet.
