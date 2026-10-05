# k6t-lint

Small linter runner. `k6t-lint.yaml` lists each script and the folders it scans.

```bash
docker run --rm -v "$PWD":/src ghcr.io/oshoval/k6t-lint:latest
```

A `k6t-lint.yaml` in the mounted repo replaces the one in the image.
