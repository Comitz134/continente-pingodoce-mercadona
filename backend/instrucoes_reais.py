# -*- coding: utf-8 -*-
"""Busca as instruções COMPLETAS reais do TheMealDB para as 67 receitas,
traduz para PT-PT e guarda o texto integral em backend/_instrucoes_pt_full.json.
A divisão em passos + normalização de temperaturas é feita por normalize_split.py.

Fonte 1 (27 receitas novas): backend/_search_full.json (instrucoes já descarregadas)
Fonte 2 (40 receitas originais): API pública do TheMealDB, procuradas pelo nome
                                  e casadas pela foto (ficheiro do thumb).

Uso:  python backend/instrucoes_reais.py
"""
import json
import re
import time
import urllib.parse
import urllib.request

API = "https://www.themealdb.com/api/json/v1/1/search.php?s=%s"
LOOKUP = "https://www.themealdb.com/api/json/v1/1/lookup.php?i=%s"
TL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt-PT&dt=t&q=%s"

# Receitas cujo nome tem "&" — a busca por nome falha; lookup direto pelo id.
FALLBACK_IDS = {
    "salmao-forno": "52959",
    "arroz-frango-chourico": "53161",
    "rotolo": "52864",
    "crumble": "52893",
}

NOVAS = {
    "tortilha-chourico", "panquecas", "panquecas-aveia", "sopa-abobora",
    "sopa-tomate", "sopa-grao", "kofta-burgers", "almondegas-borrego",
    "caril-katsu", "caril-verde", "frango-assado-argelino", "costeletas-crioula",
    "bolo-chocolate-vegan", "brownies", "cheesecake", "risotto-salmao",
    "bourguignon", "estufado-lemongrass", "sopa-noodles-salmao", "camaroes-kungpo",
    "tagine", "tonkatsu", "pho-vaca", "macarrao-pie", "salada-papaia",
    "batatas-pequeno-almoco", "estufado-irlandes",
}


def http_json(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            time.sleep(2 + i)


def translate(text):
    """Traduz EN -> PT-PT em pedaços de ~1400 chars."""
    out = []
    while text:
        chunk = text[:1400]
        if len(text) > 1400:
            cut = max(chunk.rfind(". "), chunk.rfind("\n"), 800)
            chunk = text[: cut + 1].strip()
        r = http_json(TL % urllib.parse.quote(chunk))
        out.append("".join(seg[0] for seg in r[0] if seg and seg[0]))
        text = text[len(chunk):].strip()
        time.sleep(0.4)
    return " ".join(out)


def clean_en(inst):
    """Normaliza as instruções do TheMealDB: remove marcadores 'step N', \r\n."""
    inst = inst.replace("\r\n", "\n").replace("\r", "\n")
    inst = re.sub(r"(?i)^\s*step\s*\d+[:\-\.]?\s*", "", inst, flags=re.M)
    inst = re.sub(r"\n+", "\n", inst).strip()
    return inst


def split_steps(en_text):
    """Divide em passos: primeiro por linhas/STEP, depois por frases longas."""
    # Algumas instruções vêm com STEP n por linha; já removemos o prefixo.
    lines = [ln.strip() for ln in en_text.split("\n") if ln.strip()]
    sentences = []
    for ln in lines:
        parts = re.split(r"(?<=[.!?])\s+", ln)
        sentences.extend(p for p in parts if p.strip())
    if not sentences:
        sentences = [en_text]
    # Agrupa frases muito curtas (<50 chars) com a seguinte; passo máx ~300 chars.
    steps = []
    buf = ""
    for s in sentences:
        if buf and (len(buf) < 50 or (len(buf) + len(s) < 300 and len(buf) < 220)):
            buf += " " + s
        else:
            if buf:
                steps.append(buf)
            buf = s
    if buf:
        steps.append(buf)
    return steps


def recipes():
    src = open("receitas/data.js", encoding="utf-8").read()
    out = {}
    for m in re.finditer(
        r'id: "([^"]+)", nome: "([^"]+)", nomeOrig: "([^"]+)",.*?foto: "([^"]+)"',
        src, re.DOTALL,
    ):
        out[m.group(1)] = {
            "nome": m.group(2),
            "nomeOrig": m.group(3),
            "foto": m.group(4),
            "thumb": m.group(4).split("/")[-1],
        }
    return out


def load_json_instrucoes():
    d = json.load(open("backend/_search_full.json", encoding="utf-8"))
    by_thumb = {}
    for m in d:
        by_thumb[m["foto"].split("/")[-1]] = m["instrucoes"]
    return by_thumb


def main():
    recs = recipes()
    by_thumb = load_json_instrucoes()
    en = {}
    try:
        en = json.load(open("backend/_instrucoes_en.json", encoding="utf-8"))
        print("EN ja existentes: %d (resume)" % len(en))
    except Exception:
        en = {}
    missing = []

    for rid, info in recs.items():
        inst = None
        if rid in NOVAS:
            inst = by_thumb.get(info["thumb"])
            origem = "json"
        if inst is None and rid in FALLBACK_IDS:
            try:
                res = http_json(LOOKUP % FALLBACK_IDS[rid])
                meals = res.get("meals") or []
                if meals:
                    inst = meals[0]["strInstructions"]
                    origem = "api-lookup-id"
            except Exception as e:  # noqa: BLE001
                print("ERRO lookup", rid, e)
        if inst is None:
            # Busca por nome na API e casa pela foto.
            try:
                res = http_json(API % urllib.parse.quote(info["nomeOrig"]))
                meals = res.get("meals") or []
                for m in meals:
                    if m["strMealThumb"].split("/")[-1] == info["thumb"]:
                        inst = m["strInstructions"]
                        origem = "api-nome+foto"
                        break
                if inst is None and meals:
                    inst = meals[0]["strInstructions"]
                    origem = "api-primeiro"
            except Exception as e:  # noqa: BLE001
                print("ERRO a buscar", rid, info["nomeOrig"], e)
            time.sleep(0.35)
        if inst:
            en[rid] = {"origem": origem, "en": clean_en(inst)}
        else:
            missing.append(rid)

    json.dump(en, open("backend/_instrucoes_en.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("EN obtidas: %d/%d" % (len(en), len(recs)))
    if missing:
        print("SEM instruções:", missing)

    # Traduz (com resume) e guarda o texto integral.
    pt_full = {}
    try:
        pt_full = json.load(open("backend/_instrucoes_pt_full.json", encoding="utf-8"))
        print("PT full ja existentes: %d (resume)" % len(pt_full))
    except Exception:
        pt_full = {}

    for rid, d in en.items():
        if rid in pt_full:
            continue
        try:
            t = translate(d["en"])
        except Exception as e:  # noqa: BLE001
            print("ERRO traduzir", rid, e)
            t = d["en"]
        pt_full[rid] = t
        print("  ok", rid)
        time.sleep(0.4)

    json.dump(pt_full, open("backend/_instrucoes_pt_full.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("PT full guardadas: %d" % len(pt_full))


if __name__ == "__main__":
    main()
