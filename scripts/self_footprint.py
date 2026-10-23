#!/usr/bin/env python3
"""
Pegada do self no discurso: onde aparecem os termos de dicionarios/self_identidade.csv e que palavras os acompanham.

1. Marca os termos do dicionário em cada frase dos entrevistados (corpus principal). Uma frase com termo-semente é uma
   "frase de self". Ela é "elicitada" quando a última pergunta do entrevistador tocou a mesma categoria (ELICITA).
2. Vizinhança: palavras sobrerrepresentadas nas frases de self em relação às demais frases, pela log-verossimilhança
   G² (Dunning, 1993), com ao menos 3 ocorrências nas frases de self e usadas nelas por ao menos 2 entrevistados.
   As palavras do próprio termo (o 'sou' de 'eu sou', o 'autoria') não entram na contagem.
3. Pegada na rede total: a mesma rede das 50 palavras mais frequentes de rede_semantica.py, com cada palavra colorida
   pela associação (positiva ou negativa) com as frases de self.
4. Rede da vizinhança: termos-semente (losangos) e as palavras mais associadas, em árvore máxima de Jaccard calculada
   sobre todas as frases.

Uso:
  python scripts/self_footprint.py [--k 30] [--min-semente 3]
Saída: figuras/self_pegada_rede_total.png, figuras/self_vizinhanca.png, figuras/self_vizinhanca.csv,
       figuras/self_termos.csv, figuras/self_pronomes.csv, data/self_participantes.csv (tem nomes),
       data/self_frases.csv (as frases com termos do dicionário; fica fora do git)
"""
import argparse, csv, math, os, re, sqlite3
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import spacy
from rede_semantica import (AQUI, TEXTO, preparar, lema, ler_stopwords, construir_rede, legenda_comunidades,
                            desenhar)

# Pergunta do entrevistador que torna a resposta elicitada, por categoria do dicionário
ELICITA = {
    "autodefinicao": r"\b(se considera|se v[êe]|se sente|se define|se identifica|se posiciona|se acha|"
                     r"(voc[êe]|c[êe]) [ée] (um|uma)|b[áa]sic[oa]|intermedi[áa]ri[oa]|avan[çc]ad[oa])",
    "agencia_autoria": r"\b(autor|autoria|[ée] seu|[ée] sua|m[ée]rito|respons[áa]vel|responsabilidade)",
    "self_estendido": r"\b(c[ée]rebro|mente|mem[óo]ria|cabe[çc]a|extens[ãa]o|parte de voc[êe])",
    "vocabulario_self": r"\b(identidade|imagem|autopercep|como (voc[êe]|c[êe]) [ée] vist)",
}
G2_CRITICO = [(10.83, "p < 0,001"), (6.63, "p < 0,01"), (3.84, "p < 0,05")]
# Escala divergente da skill dataviz (azul ↔ vermelho, meio cinza): do mais forte ao mais fraco em cada braço;
# cada braço passa no validador ordinal da skill (o tom mais claro com ≥ 2:1 contra a superfície)
AZUL, VERMELHO, NEUTRO = ["#184f95", "#3987e5", "#86b6ef"], ["#a8302f", "#e34948", "#ef9897"], "#d3d2cc"

def ler_dicionario(path):
    with open(path, encoding="utf-8") as f:
        dic = list(csv.DictReader(f))
    for l in dic:
        l["re"] = re.compile(l["padrao"], re.I)
        l["re_excluir"] = re.compile(l["excluir"], re.I) if l["excluir"] else None
        l["semente"] = l["semente"] == "1"
    return dic

def casar(texto, dic):
    """Termos do dicionário no texto: lista de (linha do dicionário, (início, fim))."""
    achados = []
    for l in dic:
        if l["re_excluir"] and l["re_excluir"].search(texto): continue
        achados += [(l, m.span()) for m in l["re"].finditer(texto)]
    return achados

def ler_frases(db, nlp, stop, dic):
    """Frases dos entrevistados, na ordem de rede_semantica.py, com lemas, termos do dicionário e elicitação."""
    falas, pergunta, atual = [], "", None
    for tid, quem, papel, texto in sqlite3.connect(db).execute(
            "SELECT transcricao_id, participante, papel, texto FROM turnos_analise ORDER BY transcricao_id, ordem"):
        if tid != atual: pergunta, atual = "", tid
        if papel == "entrevistador":
            if "?" in texto: pergunta = texto
        elif papel == "entrevistado":
            falas.append((quem, pergunta, texto))
    elicita = {c: re.compile(p, re.I) for c, p in ELICITA.items()}
    frases = []
    for turno, ((quem, pergunta, _), doc) in enumerate(zip(falas, nlp.pipe((preparar(t) for _, _, t in falas), batch_size=64))):
        cats_pergunta = {c for c, r in elicita.items() if r.search(pergunta)}
        for s in doc.sents:
            achados = casar(s.text, dic)
            sementes = [(l, sp) for l, sp in achados if l["semente"]]
            dentro = lambda tok: any(a <= tok.idx - s.start_char < b for _, (a, b) in sementes)
            lemas = [lema(tok, stop) for tok in s]
            cats = {l["categoria"] for l, _ in sementes}
            frases.append(dict(
                participante=quem, turno=turno, texto=s.text.strip(), pergunta=pergunta,
                lemas=[l for l in lemas if l],                                       # como em rede_semantica.py
                lemas_viz=[l for l, tok in zip(lemas, s) if l and not dentro(tok)],  # sem as palavras do termo
                termos=sorted({l["termo"] for l, _ in sementes}), categorias=sorted(cats),
                todos_termos=sorted({l["termo"] for l, _ in achados}),
                pronome=any(l["categoria"] == "pronomes_1a_pessoa" for l, _ in achados),
                self=bool(sementes), elicitada=bool(cats & cats_pergunta)))
    return frases

def g2(a, b, c, d):
    """Log-verossimilhança de Dunning para a ocorrências em c (alvo) contra b em d (referência); sinal = direção."""
    e1, e2 = c * (a + b) / (c + d), d * (a + b) / (c + d)
    v = 2 * sum(o * math.log(o / e) for o, e in ((a, e1), (b, e2)) if o)
    return v if a / c >= b / d else -v

def contraste(alvo, resto, chave="lemas_viz"):
    """G² de cada palavra entre dois grupos de frases, com contagens e o número de participantes que a usam no grupo
    em que ela é mais frequente (no alvo, se G² > 0)."""
    ca, cr = Counter(l for f in alvo for l in f[chave]), Counter(l for f in resto for l in f[chave])
    quem = {"alvo": defaultdict(set), "resto": defaultdict(set)}
    for g, fs in (("alvo", alvo), ("resto", resto)):
        for f in fs:
            for l in f[chave]: quem[g][l].add(f["participante"])
    c, d = sum(ca.values()), sum(cr.values())
    out = {}
    for w in set(ca) | set(cr):
        v = g2(ca[w], cr[w], c, d)
        out[w] = dict(g2=v, no_alvo=ca[w], no_resto=cr[w], participantes=len(quem["alvo" if v >= 0 else "resto"][w]),
                      razao=(ca[w] / c) / (cr[w] / d) if cr[w] else float("inf"))
    return out

def em_janela(frases, marcadas, janela):
    """Frases marcadas mais as `janela` frases antes e depois, no mesmo turno."""
    sel = set()
    for i in marcadas:
        sel.update(j for j in range(max(0, i - janela), min(len(frases), i + janela + 1))
                   if frases[j]["turno"] == frases[i]["turno"])
    return [frases[j] for j in sorted(sel)], [f for j, f in enumerate(frases) if j not in sel]

def faixa(v):
    """Cor da palavra na pegada: azul (mais nas frases de self), vermelho (menos) ou cinza (sem diferença)."""
    for i, (crit, _) in enumerate(G2_CRITICO):
        if abs(v) >= crit: return (AZUL if v > 0 else VERMELHO)[i]
    return NEUTRO

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/entrevistas.db")
    ap.add_argument("--dicionario", default=os.path.join(os.path.dirname(AQUI), "dicionarios", "self_identidade.csv"))
    ap.add_argument("--stopwords", default=os.path.join(AQUI, "stopwords_rede.txt"))
    ap.add_argument("--k", type=int, default=30, help="máximo de palavras da vizinhança na rede")
    ap.add_argument("--min-semente", type=int, default=3, help="frases mínimas para um termo virar nó")
    ap.add_argument("--janela", type=int, default=0, help="frases vizinhas (no mesmo turno) somadas às frases de self")
    ap.add_argument("--saida", default="figuras/self")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    dic = ler_dicionario(a.dicionario)
    nlp = spacy.load("pt_core_news_sm", disable=["ner"])
    frases = ler_frases(a.db, nlp, ler_stopwords(a.stopwords), dic)
    selfs = [f for f in frases if f["self"]]
    espont = [f for f in selfs if not f["elicitada"]]
    print(f"{len(frases)} frases; {len(selfs)} com termo-semente ({len(selfs) / len(frases):.1%}), "
          f"{len(selfs) - len(espont)} delas elicitadas")
    contexto, outras = em_janela(frases, [i for i, f in enumerate(frases) if f["self"]], a.janela)
    contexto_esp, outras_esp = em_janela(frases, [i for i, f in enumerate(frases) if f["self"] and not f["elicitada"]], a.janela)
    if a.janela: print(f"com a janela de ±{a.janela} frase(s): {len(contexto)} frases de contexto")

    # termos e participantes
    os.makedirs(os.path.dirname(a.saida) or ".", exist_ok=True)
    with open(a.saida + "_termos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["categoria", "termo", "semente", "frases", "participantes", "frases_elicitadas"])
        for l in dic:
            fs = [x for x in frases if l["termo"] in x["todos_termos"]]
            w.writerow([l["categoria"], l["termo"], int(l["semente"]), len(fs), len({x["participante"] for x in fs}),
                        sum(x["elicitada"] for x in fs if l["termo"] in x["termos"])])
    with open("data/self_participantes.csv", "w", encoding="utf-8-sig", newline="") as f:   # tem nomes: fora do git
        w = csv.writer(f)
        w.writerow(["participante", "frases", "frases_self", "pct_self", "frases_self_espontaneas", "pct_pronome_1a_pessoa"])
        for p in sorted({x["participante"] for x in frases}):
            fs = [x for x in frases if x["participante"] == p]
            n_self = sum(x["self"] for x in fs)
            w.writerow([p, len(fs), n_self, round(100 * n_self / len(fs), 1),
                        sum(x["self"] and not x["elicitada"] for x in fs), round(100 * sum(x["pronome"] for x in fs) / len(fs), 1)])
    with open("data/self_frases.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["participante", "termos", "categorias", "elicitada", "pergunta_anterior", "frase"])
        w.writerows([x["participante"], "; ".join(x["termos"]), "; ".join(x["categorias"]), int(x["elicitada"]),
                     x["pergunta"][-200:], x["texto"]] for x in selfs)

    # vizinhança: contraste das frases de self com as demais; robustez só com as espontâneas
    viz = contraste(contexto, outras)
    viz_esp = contraste(contexto_esp, [f for f in outras_esp if not f["self"]])
    validas = sorted((w for w, r in viz.items() if r["g2"] >= G2_CRITICO[-1][0] and r["no_alvo"] >= 3
                      and r["participantes"] >= 2), key=lambda w: -viz[w]["g2"])
    with open(a.saida + "_vizinhanca.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["palavra", "g2", "nas_frases_self", "nas_demais", "razao_de_frequencia", "participantes",
                    "g2_so_espontaneas", "na_rede"])
        w.writerows([p, round(viz[p]["g2"], 2), viz[p]["no_alvo"], viz[p]["no_resto"], round(viz[p]["razao"], 2),
                     viz[p]["participantes"], round(viz_esp.get(p, {"g2": 0})["g2"], 2), int(i < a.k)]
                    for i, p in enumerate(validas))
    print(f"vizinhança: {len(validas)} palavras com G² ≥ 3,84 (≥ 3 ocorrências, ≥ 2 entrevistados)")
    print("  " + ", ".join(f"{p} ({viz[p]['g2']:.1f})" for p in validas[:a.k]))

    # pronomes de 1ª pessoa: só a pegada, contra as frases sem pronome
    com_eu = [f for f in frases if f["pronome"]]
    pron = contraste(com_eu, [f for f in frases if not f["pronome"]])
    sig = sorted((w for w, r in pron.items() if abs(r["g2"]) >= 6.63 and r["participantes"] >= 2), key=lambda w: -pron[w]["g2"])
    with open(a.saida + "_pronomes.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["palavra", "g2", "nas_frases_com_eu", "nas_demais", "participantes"])
        w.writerows([p, round(pron[p]["g2"], 2), pron[p]["no_alvo"], pron[p]["no_resto"], pron[p]["participantes"]] for p in sig)
    print(f"pronomes de 1ª pessoa em {len(com_eu) / len(frases):.0%} das frases; mais com 'eu': "
          + ", ".join(w for w in sig if pron[w]["g2"] > 0) + "; mais sem 'eu': "
          + ", ".join(w for w in sig[::-1] if pron[w]["g2"] < 0))

    # 3. pegada na rede total (mesma rede de rede_semantica.py)
    us = [f["lemas"] for f in frases if f["lemas"]]
    freq = Counter(l for u in us for l in u)
    topo = [w for w, _ in freq.most_common(50)]
    _, T, _ = construir_rede(us, topo, "jaccard", a.seed)
    cor = {n: faixa(viz.get(n, {"g2": 0})["g2"]) for n in T}
    alca = lambda c: plt.Line2D([], [], ls="", marker="o", ms=9, mfc=c, mec="none")
    vazio = (plt.Line2D([], [], ls="", marker=""), "")   # a legenda preenche por coluna: azul | cinza | vermelho
    legenda = ([(alca(AZUL[i]), f"mais nas frases de self, {r}") for i, (_, r) in enumerate(G2_CRITICO)]
               + [(alca(NEUTRO), "sem diferença"), vazio, vazio]
               + [(alca(VERMELHO[i]), f"menos nas frases de self, {r}") for i, (_, r) in enumerate(G2_CRITICO)])
    n_azul = sum(viz.get(n, {"g2": 0})["g2"] >= 3.84 for n in T)
    n_verm = sum(viz.get(n, {"g2": 0})["g2"] <= -3.84 for n in T)
    desenhar(T, freq, a.saida + "_pegada_rede_total.png", "Pegada do self na rede semântica total",
             f"A mesma rede das 50 palavras mais frequentes, colorida pela associação de cada palavra com as {len(contexto)} frases "
             f"de autodefinição, autoria, self estendido e vocabulário do self (G² de Dunning, contra as {len(outras)} demais"
             + (f"; janela de ±{a.janela} frase" if a.janela else "") + f"). {n_azul} das 50 palavras são mais frequentes "
             f"nas frases de self e {n_verm} menos frequentes.",
             a.seed, cor, legenda, "Associação com as frases de self", ncol=3)

    # 4. rede da vizinhança: sementes + palavras mais associadas
    n_termo = Counter(t for f in selfs for t in f["termos"])
    sementes = [t for t, n in n_termo.most_common() if n >= a.min_semente]
    vizinhas = validas[:a.k]
    us_viz = [f["lemas_viz"] + f["termos"] for f in frases]
    _, Tv, comunidades = construir_rede(us_viz, sementes + vizinhas, "jaccard", a.seed)
    n_viz = Counter(l for f in contexto for l in set(f["lemas_viz"]))
    tam = {**{p: n_viz[p] for p in vizinhas}, **{t: n_termo[t] for t in sementes}}
    cor_v, legenda_v = legenda_comunidades(Tv, comunidades, tam)
    forma = {t: "D" for t in sementes}
    legenda_v += [(plt.Line2D([], [], ls="", marker="D", ms=8, mfc="none", mec=TEXTO), "termo do dicionário (itálico)"),
                  (plt.Line2D([], [], ls="", marker="o", ms=9, mfc="none", mec=TEXTO), "palavra da vizinhança")]
    desenhar(Tv, tam, a.saida + "_vizinhanca.png", "Vizinhança do self no discurso dos entrevistados",
             f"Termos do dicionário com ao menos {a.min_semente} frases (losangos) e as {len(vizinhas)} palavras mais associadas "
             f"às frases de self (G² ≥ 3,84; ao menos 3 ocorrências e 2 entrevistados). Tamanho = nº de frases de self em que "
             f"aparece; árvore máxima de Jaccard em todas as {len(frases)} frases; cores = comunidades (Louvain).",
             a.seed, cor_v, legenda_v, "Comunidades (palavras mais presentes de cada uma) e formas", forma=forma)
    print("sementes na rede: " + ", ".join(f"{t} ({n_termo[t]})" for t in sementes))
    for c, g in enumerate(comunidades, 1):
        print(f"  {c}: " + ", ".join(sorted(g, key=lambda n: -tam[n])))
    print(f"figuras: {a.saida}_pegada_rede_total.png, {a.saida}_vizinhanca.png")

if __name__ == "__main__":
    main()
