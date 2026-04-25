# GitHub Publishing

## Normalized Names

Use these exact names for public publishing:

| Surface | Value |
| --- | --- |
| Owner | `AIandI0x1` |
| Repository | `hermes-hackathon-hub` |
| Full name | `AIandI0x1/hermes-hackathon-hub` |
| Default branch | `main` |
| Plugin folder | `hermes-hackathon-hub` |
| Manifest name | `hermes-hackathon-hub` |
| Dashboard route | `/plugins` |

## Create Public Repository

After validation and user confirmation:

```bash
gh repo create AIandI0x1/hermes-hackathon-hub \
  --public \
  --source=. \
  --remote=origin \
  --push
```

## Install Command For README And Discord

```bash
mkdir -p ~/.hermes/plugins
git clone https://github.com/AIandI0x1/hermes-hackathon-hub \
  ~/.hermes/plugins/hermes-hackathon-hub
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

## Release Tags

Use semantic tags:

```text
v0.1.0
v0.2.0
```

The hackathon entry should start as `v0.1.0`.
