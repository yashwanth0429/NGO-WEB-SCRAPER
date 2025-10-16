import os, sys, re, time
from datetime import datetime
import yaml, requests, pandas as pd
from bs4 import BeautifulSoup

# Identify as a regular browser to avoid primitive bot blocks
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"}
# Generic phone pattern; site-specific patterns can be layered via YAML
PHONE_RE = re.compile(r"(?:\+?\d[\s-]?){7,15}\d", re.M | re.I)

# Resolve relative file paths against this script's folder
def rpath(p): 
    return p if os.path.isabs(p) else os.path.join(os.path.dirname(__file__), p)

# Load config (ngos.yaml) into a Python dict
def load_yaml(p):
    p = rpath(p)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Fetch a URL once; return parsed soup and raw HTML
def fetch(url):
    r = requests.get(url, headers=UA, timeout=20); r.raise_for_status()
    h = r.text
    return BeautifulSoup(h, "lxml"), h

# Read the site/brand name from Open Graph; fall back to <title> or first <h1>
def get_og_name(soup):
    tag = soup.find("meta", {"property": "og:site_name"}) or soup.find("meta", {"name": "og:site_name"})
    if tag and tag.get("content"): 
        return tag["content"].strip()
    if soup.title and soup.title.string: 
        return soup.title.string.strip()
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else None

# Apply generic rules: either take a static value or the first regex match
def apply_rules(text, rules):
    if rules.get("static"):
        return "; ".join(rules["static"]) if isinstance(rules["static"], (list, tuple)) else rules["static"]
    for pat in rules.get("regex_any", []):
        m = re.search(pat, text, re.I | re.S)
        if m: 
            return m.group(0).strip()
    return None

# Gather phone numbers, deduplicate, prioritize, and ensure a minimum count
def extract_phones(text, rules):
    phones = []
    if "regex_any" in rules:
        for pat in rules["regex_any"]:
            phones += [m.group(0) for m in re.finditer(pat, text, re.I)]
    else:
        phones = [m.group(0) for m in PHONE_RE.finditer(text)]
    phones = list(dict.fromkeys(phones))
    prefer = rules.get("prefer", [])
    if prefer:
        pref = re.compile("(" + "|".join(prefer) + ")", re.I)
        phones.sort(key=lambda p: 0 if pref.search(p) else 1)
    k = max(1, rules.get("required_min", 1))
    return ", ".join(phones[:max(k, 3)]) if len(phones) >= k else None

# Hard fail if a required field is missing (no placeholders)
def require(v, field, domain):
    if not v or (isinstance(v, str) and not v.strip()):
        raise ValueError(f"{domain}: missing required field -> {field}")
    return v

def scrape_domain(domain, cfg):
    # Fetch each declared contact page exactly once and combine text
    soups, texts = [], []
    for u in cfg["contact_pages"]:
        s, _ = fetch(u); soups.append(s); texts.append(s.get_text(" ", strip=True))
    text = " ".join(texts)

    # NGO Name from OG tag on first page or configured URL
    og_url = cfg.get("selectors", {}).get("og_name", {}).get("url") or cfg["contact_pages"][0]
    og_soup = soups[0] if og_url == cfg["contact_pages"][0] else fetch(og_url)[0]
    ngo_name = require(get_og_name(og_soup), "NGO Name", domain)

    # Field extraction via config rules
    sel = cfg["selectors"]
    address  = require(apply_rules(text, sel["address"]),   "Address",         domain)
    phones   = require(extract_phones(text, sel["phones"]), "Contact Number",  domain)
    services = require(apply_rules("",  sel["services"]),   "Services Offered",domain)

    # Contact person from static or regex; optionally from a specific page
    cp, cpsel = None, sel["contact_person"]
    if cpsel.get("static"):
        cp = cpsel["static"]
    else:
        ctext = text
        if "page" in cpsel and cpsel["page"] not in cfg["contact_pages"]:
            ctext = fetch(cpsel["page"])[0].get_text(" ", strip=True)
        m = re.search(cpsel.get("regex", r"$a"), ctext, re.I | re.S)
        if m:
            name  = m.group(1).strip()
            phone = m.group(2).strip() if m.lastindex and m.lastindex >= 2 and m.group(2) else ""
            cp = cpsel.get("format", "{name} {phone}").format(name=name, phone=phone).strip()
    require(cp, "Contact Person", domain)

    return {
        "NGO Name": ngo_name,
        "Website":  f"https://{domain}/",
        "Address":  address,
        "Services Offered": services if isinstance(services, str) else "; ".join(services),
        "Contact Person":  cp,
        "Contact Number":  phones,
        "Source Pages": "; ".join(cfg["contact_pages"])
    }

def main():
    # 1) Start: show which config file is used
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "ngos.yaml"
    print(f"[1/5] Loading config: {cfg_path}")

    cfg = load_yaml(cfg_path)

    rows = []
    for i, (domain, c) in enumerate(cfg.items(), start=1):
        # 2) Domain progress
        print(f"[2/5] ({i}/{len(cfg)}) Scraping: {domain}")
        rows.append(scrape_domain(domain, c))

    # 3) Validation success summary
    print(f"[3/5] Validation passed for {len(rows)} domain(s). Preparing Excel...")

    df = pd.DataFrame(
        rows, 
        columns=["NGO Name","Website","Address","Services Offered","Contact Person","Contact Number","Source Pages"]
    )
    out_dir = rpath("out"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"ngo_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    # 4) Show where the file will be saved
    print(f"[4/5] Writing file: {out}")
    df.to_excel(out, index=False)

    # 5) Done
    print(f"[5/5] Done. Saved {len(df)} rows -> {out}")

if __name__ == "__main__":
    main()
