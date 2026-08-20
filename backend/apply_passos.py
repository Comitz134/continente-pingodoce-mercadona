# -*- coding: utf-8 -*-
"""Aplica os passos reais (backend/_instrucoes_pt.json) no receitas/data.js.

Uso:  python backend/apply_passos.py
"""
import json
import re


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def js_arr(steps):
    return "[" + ", ".join(js_str(s) for s in steps) + "]"


def main():
    passos = json.load(open("backend/_instrucoes_pt.json", encoding="utf-8"))
    path = "receitas/data.js"
    src = open(path, encoding="utf-8").read()
    missing = []
    for rid, steps in passos.items():
        m = re.search(r'id: "%s"' % re.escape(rid), src)
        if not m:
            missing.append(rid)
            continue
        p = src.find("passos: ", m.end())
        e = src.find("],", p)
        if p == -1 or e == -1:
            missing.append(rid)
            continue
        src = src[:p] + "passos: " + js_arr(steps) + "," + src[e + 2:]
    open(path, "w", encoding="utf-8").write(src)
    print("data.js: %d/%d receitas atualizadas" % (len(passos) - len(missing), len(passos)))
    if missing:
        print("FALTARAM:", missing)


if __name__ == "__main__":
    main()
