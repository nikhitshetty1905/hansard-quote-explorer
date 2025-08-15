# tagger.py
# Adds a 'frame' label per quote using transparent keyword rules.

import json, re

IN_FILE  = "quotes_premium.jsonl"
OUT_FILE = "quotes_premium_tagged.jsonl"

RULES = {
  "LABOUR_NEED": [
    r"(labour|labor)\s+shortage", r"manpower\s+(?:shortage|need)",
    r"(fill|filled|filling)\s+(?:vacanc|shortage|gaps?)",
    r"essential\s+(?:workers|workforce|labou?r)"
  ],
  "LABOUR_THREAT": [
    r"(depress(?:ing)?|lower(?:ing)?)\s+wage[s]?",
    r"(job[s]?\s+competition|taking\s+our\s+jobs?)",
    r"surplus\s+labou?r", r"unemployment\s+(?:rise|increase|pressure)"
  ],
  "RACIALISED": [
    r"\baliens?\b", r"\bundesirable[s]?\b", r"\bcolou?red\b",
    r"racial|race\s+problem", r"\bforeigner[s]?\b.*(undesirable|inferior|threat)",
  ]
}

def label(text):
    text_l = text.lower()
    hits = []
    for frame, pats in RULES.items():
        for p in pats:
            if re.search(p, text_l):
                hits.append(frame); break
    if not hits: return "OTHER"
    if len(hits) == 1: return hits[0]
    # prioritise RACIALISED if present; else mark MIXED
    if "RACIALISED" in hits: return "RACIALISED"
    return "MIXED"

with open(IN_FILE, "r", encoding="utf-8") as fin, open(OUT_FILE, "w", encoding="utf-8") as fout:
    for line in fin:
        rec = json.loads(line)
        rec["frame"] = label(rec["quote"])
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Tagged -> {OUT_FILE}")