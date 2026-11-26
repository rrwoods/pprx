# Nginx Reverse Proxy in Front of Gunicorn

This project does not manage a custom `nginx` reverse-proxy container or DigitalOcean App Platform component in front of `gunicorn`.

## Why this is out of scope

The application is deployed on DigitalOcean App Platform using the default Python buildpack running `gunicorn --workers=1 --worker-tmp-dir /dev/shm pprxweb.wsgi`. DigitalOcean App Platform's managed ingress already handles TLS termination, HTTP routing, and reverse proxying in front of `gunicorn`, so adding and maintaining a separate `nginx` Docker component adds operational complexity without solving a current need.

## Prior requests

- #22: "Put nginx in front of gunicorn"
