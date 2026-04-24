# WORKPLAN — krshi27-scribe

**Status**: Streamlit app works locally. `environment.yml` created for Streamlit Cloud. GitHub mirror exists.
**Output**: B&W Voronoi stencil from text — printable as fine art print, sticker, or stencil.
**Params**: `text`, `size`, `n_shift`, `shift_range`, `line_width`, `seed` — all serializable → natural preset target.

---

## Prerequisite (~20min, before anything else)

- [x] **SCRIBE-ENV**: Create `environment.yml` — required for Streamlit Cloud:

  ```yaml
  name: krshi27-scribe
  channels:
    - conda-forge
  dependencies:
    - python=3.14
    - numpy
    - pillow
    - matplotlib
    - scipy
    - shapely
    - streamlit
    - pip:
        - -e .
  ```

## This sprint (Apr 24 – May 1)

- [ ] **SCRIBE-1** ~1hr: Deploy to Streamlit Cloud — create `environment.yml` first, connect `github.com/krshI27/krshi27-scribe`, test render end-to-end
- [x] **ZV1-SCRIBE** ~1hr: Add `?preset=` URL loader (see pattern below) — 6 params map directly to `st.session_state`; test round-trip with a saved preset URL

## Next sprint

- [x] **SCRIBE-EXPORT** ~1hr: Add high-res download button — `render(text, size=3508)` at A4@300dpi (2480×3508px); `PIL.Image.save(buf, "JPEG", dpi=(300,300))`; `st.download_button`
- [ ] **SCRIBE-PRODIGI** ~1hr: Add "Order Print" button → call high-res render → upload PNG to R2 public bucket → `POST https://api.prodigi.com/v4.0/orders` with `GLOBAL-FAP-11.7X8.3` SKU (A4 fine art print)
- [ ] **SCRIBE-STICKER** ~30min: Evaluate sticker SKU (`GLOBAL-STK-*`) — B&W Voronoi type is ideal for sticker; check Prodigi sticker specs (white background needed?)
- [ ] **ZV1-preset-scribe** ~30min: Create 2–3 Zine Vol.1 candidate presets — save as `presets/zine-vol1-*.json`

## Preset loader pattern (Streamlit)

```python
import json
import streamlit as st

_raw = st.query_params.get("preset")
if _raw:
    try:
        _p = json.loads(_raw)
        for k, v in _p.get("params", {}).items():
            st.session_state.setdefault(k, v)
    except (json.JSONDecodeError, KeyError):
        pass
# widgets use key= matching params keys, e.g. st.slider("size", ..., key="size")
```

## Preset schema

```json
{
  "name": "Zine Vol.1 — KRSHI27 Voronoi",
  "app": "krshi27-scribe",
  "params": {
    "text": "KRSHI27",
    "size": 512,
    "n_shift": 10,
    "shift_range": 0.0125,
    "line_width": 2.0,
    "seed": 42
  }
}
```

## Prodigi order pattern (same across all apps)

```python
import requests, uuid, boto3, io

def upload_to_r2(img_bytes: bytes, key: str, secrets) -> str:
    s3 = boto3.client("s3", endpoint_url=secrets["R2_ENDPOINT"],
                      aws_access_key_id=secrets["R2_ACCESS_KEY"],
                      aws_secret_access_key=secrets["R2_SECRET_KEY"])
    s3.put_object(Bucket="krshi27-prints", Key=key, Body=img_bytes,
                  ContentType="image/jpeg", ACL="public-read")
    return f"{secrets['R2_PUBLIC_URL']}/{key}"

def create_prodigi_order(image_url: str, sku: str, recipient: dict, api_key: str) -> dict:
    resp = requests.post(
        "https://api.prodigi.com/v4.0/orders",
        json={
            "merchantReference": f"order-{uuid.uuid4().hex[:8]}",
            "shippingMethod": "Standard",
            "recipient": recipient,
            "items": [{"merchantReference": "item-1", "sku": sku, "copies": 1,
                        "sizing": "fillPrintArea",
                        "assets": [{"printArea": "default", "url": image_url}]}],
        },
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()
```

## Notes

- `render()` returns PIL Image — resize to 3508px height for A4@300dpi before upload
- No external data deps, no R2 needed for the render itself — simplest deploy in portfolio
- GitHub mirror: `git@github-krshi27:krshI27/krshi27-scribe.git` (confirmed in remotes)
- Prodigi API key in `.streamlit/secrets.toml` (gitignored) — same key as brixels
