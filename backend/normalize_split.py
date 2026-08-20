# -*- coding: utf-8 -*-
"""Normaliza as temperaturas (ex.: '190C' -> '190 °C', 'gás 5' removido)
e divide em passos o texto integral de backend/_instrucoes_pt_full.json,
gravando o resultado em backend/_instrucoes_pt.json (id -> [passos]).

Uso:  python backend/normalize_split.py
"""
import json
import re


def normalize(t):
    # 350 graus F (175 graus C) -> 175 °C
    t = re.sub(r"(\d+)\s*graus\s*F\s*\(\s*(\d+)\s*graus\s*C\s*\)", r"\2 °C", t)
    # 180 graus C -> 180 °C  |  180 graus -> 180 °C
    t = re.sub(r"(\d+)\s*graus\s*C\b", r"\1 °C", t)
    t = re.sub(r"(\d+)\s*graus\b", r"\1 °C", t)
    # ventilação/ventilador/ventilar N C -> N °C (ventilado)
    t = re.sub(r"ventila[çc][aã]o\s*(\d+)\s*°?C\b", r"\1 °C (ventilado)", t)
    t = re.sub(r"ventila[dr]\s*(\d+)\s*°?C\b", r"\1 °C (ventilado)", t)
    # convencional N C -> N °C
    t = re.sub(r"convencional\s*(\d+)\s*°?C\b", r"\1 °C", t)
    # 190C / 190 °C -> 190 °C
    t = re.sub(r"(\d+)\s*°?C\b", r"\1 °C", t)
    # remove marca de gás britânica: gás 4, gás 1/4
    t = re.sub(r"/?\s*g[aá]s\s*\d+(?:\s*[\/⁄]\s*\d+)?", "", t)
    # limpa barras duplas, caracteres invisíveis e espaços
    t = re.sub(r"\s*/\s*", " / ", t)
    for ch in "\u200b\u200c\u200d\ufeff\u00ad":
        t = t.replace(ch, "")
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # fragmento (ex.: abreviação falsa) junta-se ao anterior
        if sentences and (len(p) < 30 or not re.match(r"^[A-ZÀ-Ý0-9\"'(]", p)):
            sentences[-1] = sentences[-1] + " " + p
        else:
            sentences.append(p)
    # agrupa frases em passos de ~220 chars
    steps = []
    buf = ""
    for s in sentences:
        if not buf:
            buf = s
        elif len(buf) + len(s) + 1 <= 220:
            buf += " " + s
        else:
            steps.append(buf)
            buf = s
    if buf:
        steps.append(buf)
    return steps


def main():
    full = json.load(open("backend/_instrucoes_pt_full.json", encoding="utf-8"))
    out = {}
    for rid, text in full.items():
        out[rid] = split_sentences(normalize(text))
    json.dump(out, open("backend/_instrucoes_pt.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    n = sum(len(v) for v in out.values())
    print("OK: %d receitas, %d passos totais" % (len(out), n))


if __name__ == "__main__":
    main()
