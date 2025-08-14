import os, sys, time, json, re
from datetime import datetime
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

def _clean_env(name, required=False):
    v = os.getenv(name)
    if v is None:
        if required:
            print(f"ENV manquant: {name}", file=sys.stderr)
            sys.exit(1)
        return None
    v = v.strip()
    if " #" in v:
        v = v.split(" #", 1)[0].strip()
    return v or None

AIRTABLE_PAT      = _clean_env("AIRTABLE_PAT", required=True)
BASE_ID           = _clean_env("AIRTABLE_BASE_ID", required=True)
TABLE             = _clean_env("AIRTABLE_TABLE_NAME", required=True)
VIEW              = _clean_env("AIRTABLE_VIEW_NAME")
OMDB_API_KEY      = _clean_env("OMDB_API_KEY", required=True)
POSTER_MODE       = (_clean_env("POSTER_MODE") or "attachment").lower()
RATE_LIMIT_MS     = int(_clean_env("RATE_LIMIT_MS") or "120")

AT_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}

def at_list_records():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{requests.utils.quote(TABLE, safe='')}"
    params = {
        "pageSize": 100,
        "fields[]": ["Title","Année","Rating","Poster","Director","Movie release date","IMDB Link"]
    }
    if VIEW:
        params["view"] = VIEW
    out, offset = [], None
    while True:
        q = params.copy()
        if offset:
            q["offset"] = offset
        r = requests.get(url, headers=AT_HEADERS, params=q, timeout=30)
        if r.status_code == 401:
            print("401 Unauthorized: vérifie PAT et droits sur la base.", file=sys.stderr)
            sys.exit(1)
        r.raise_for_status()
        data = r.json()
        out.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        time.sleep(0.22)
    return out

def at_update_batch(batch):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{requests.utils.quote(TABLE, safe='')}"
    payload = {"records": batch, "typecast": False}
    r = requests.patch(url, headers=AT_HEADERS, data=json.dumps(payload), timeout=60)
    if r.status_code >= 400:
        print("Erreur Airtable:", r.status_code, r.text[:500], file=sys.stderr)
        r.raise_for_status()
    return r.json()

def parse_omdb_date(s):
    if not s or s == "N/A":
        return None
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        d = datetime.fromisoformat(s)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return None

def omdb_lookup(title, year=None):
    params = {"t": title, "apikey": OMDB_API_KEY}
    if year:
        params["y"] = str(year)
    url = f"https://www.omdbapi.com/?{urlencode(params)}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") == "True":
            return {
                "imdbRating": None if data.get("imdbRating") in (None,"N/A") else data.get("imdbRating"),
                "Poster": None if data.get("Poster") in (None,"N/A") else data.get("Poster"),
                "Director": None if data.get("Director") in (None,"N/A") else data.get("Director"),
                "Released": parse_omdb_date(data.get("Released")),
                "imdbID": None if data.get("imdbID") in (None,"N/A") else data.get("imdbID"),
            }
        return None
    except requests.RequestException:
        return None

def normalize_year(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        m = re.search(r"\d{4}", val)
        return int(m.group(0)) if m else None
    return None

def build_fields_from_omdb(hit, poster_mode):
    fields = {}
    if hit["imdbRating"] is not None:
        try:
            fields["Rating"] = float(hit["imdbRating"])
        except ValueError:
            fields["Rating"] = None
    else:
        fields["Rating"] = None
    if poster_mode == "attachment":
        fields["Poster"] = [{"url": hit["Poster"]}] if hit["Poster"] else []
    else:
        fields["Poster"] = hit["Poster"] if hit["Poster"] else None
    fields["Director"] = hit["Director"] if hit["Director"] else None
    fields["Movie release date"] = hit["Released"] if hit["Released"] else None
    fields["IMDB Link"] = hit["imdbID"] if hit["imdbID"] else None
    return fields

def main():
    print("Démarrage script", flush=True)
    recs = at_list_records()
    total = len(recs)
    print(f"Records à traiter: {total}", flush=True)

    updates = []
    processed = 0
    found = 0

    for rec in recs:
        fields = rec.get("fields", {})
        title = (fields.get("Title") or "").strip()
        year = normalize_year(fields.get("Année"))
        if not title:
            processed += 1
            continue
        hit = omdb_lookup(title, year)
        time.sleep(RATE_LIMIT_MS / 1000.0)
        if hit:
            found += 1
            updates.append({"id": rec["id"], "fields": build_fields_from_omdb(hit, POSTER_MODE)})
        processed += 1
        if len(updates) >= 10:
            print(f"Envoi batch de {len(updates[:10])} maj", flush=True)
            at_update_batch(updates[:10])
            updates = updates[10:]
        if processed % 10 == 0:
            print(f"Progression: {processed}/{total} (trouvés {found})", flush=True)

    if updates:
        print(f"Envoi batch final de {len(updates)} maj", flush=True)
        at_update_batch(updates)
    print(f"Terminé. Traités {processed}, trouvés {found} correspondances.", flush=True)

if __name__ == "__main__":
    main()
