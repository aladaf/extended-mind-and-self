#!/usr/bin/env python3
"""
Rede relacional "quem faz o quê a quem" entre o falante e a IA, a partir da sintaxe das frases que mencionam a IA
(gramática semântica sujeito–ação–objeto; Franzosi, 2010, Quantitative Narrative Analysis).

Para cada menção à IA em data/ia_mencoes.csv (as 656 frases da extração de ia_enquadramento.py), o spaCy
(pt_core_news_md) dá a árvore de dependências e o script tira triplas (sujeito, verbo, objeto):
  atores    'eu' = eu, me, mim, comigo, a gente, nós e o sujeito oculto de 1ª pessoa (pela morfologia do verbo);
            'IA' = os termos da IA e, nas frases que entraram por anáfora ou depois de um termo, ele/ela/eles/elas
  papel     da IA no verbo, pela preposição logo antes dela (mais robusta que a análise sintática na fala transcrita):
            pro/pra/para = destinatário; na/no/em = recipiente; com = parceria só com 'junto' ou verbo de troca
            (conversar, discutir…), senão instrumento como 'na'; sem preposição = sujeito (antes do verbo e marcada
            como sujeito) ou objeto. Sem verbo que governe a IA, a frase não gera tripla.
  negação   'não', 'nunca', 'nem', 'jamais' ligados ao verbo
  cópula    "a IA (não) é X" vira o atributo X
Cada tripla cai num tipo de ligação: eu → IA (objeto ou recipiente), eu → IA (destinatário), eu com IA, IA → eu,
IA age (sem o falante como objeto), IA é / não é.

A rede não usa a codificação manual; ela só é comparada com ela no fim (concordância por frase, kappa).

Uso:
  python scripts/rede_relacional.py [--min 2]
Saída: data/ia_triplas.csv (com as frases), figuras/ia_rede_relacional.png e figuras/ia_rede_relacional_arestas.csv
"""
import argparse, csv, math, re
from collections import Counter, defaultdict
import spacy
from rede_semantica import CORES, SUPERFICIE, TEXTO, TEXTO_2, preparar, lema_verbo
from ia_enquadramento import SIGLAS_IA, TERMOS_IA, POLO, ler_csv

PRONOMES_IA = {"ele", "ela", "eles", "elas"}
EU_SUJEITO = {"eu", "gente", "nós"}
EU_OBJETO = {"me", "mim", "comigo"}
NEGACAO = {"não", "nunca", "nem", "jamais"}
PREP = {**dict.fromkeys(["pro", "pra", "para", "pros", "pras"], "destinatário"), "com": "com",
        **dict.fromkeys(["na", "no", "nas", "nos", "em", "num", "numa", "dentro"], "recipiente")}
# 'com' é companhia ou instrumento ("faço sites com essas ferramentas"); só é parceria com 'junto' antes ou com verbo de troca
VERBOS_TROCA = {"conversar", "discutir", "debater", "dialogar", "trocar", "brigar", "interagir", "colaborar", "conviver"}
TIPOS = ["eu → IA", "eu → IA (pra/pro)", "eu com IA", "IA → eu", "IA age", "IA é"]

def eh_ia(tok, frase_por_anafora):
    if SIGLAS_IA.fullmatch(tok.text) or TERMOS_IA.fullmatch(tok.text): return True
    if tok.lower_ in PRONOMES_IA:   # pronome: só se a frase entrou por anáfora ou se a IA foi nomeada antes nela
        return frase_por_anafora or any(SIGLAS_IA.fullmatch(t.text) or TERMOS_IA.fullmatch(t.text) for t in tok.doc[:tok.i])
    return False

def verbo_de(tok):
    """Sobe na árvore até o verbo que governa o token (ou até um predicado nominal com cópula)."""
    h = tok.head
    while h != h.head and h.pos_ not in ("VERB", "AUX") and not any(c.dep_ == "cop" for c in h.children):
        h = h.head
    return h

def lema_v(v):
    return lema_verbo(v.text.lower(), v.lemma_.lower()) if v.pos_ == "VERB" else v.lemma_.lower()

def negado(v):
    return any(c.lower_ in NEGACAO for c in v.children)

def sujeito(v):
    """'eu', 'IA', 'outro' ou None: sujeito explícito do verbo, ou o oculto de 1ª pessoa pela morfologia."""
    for c in v.children:
        if c.dep_ in ("nsubj", "nsubj:pass"):
            return "eu" if c.lower_ in EU_SUJEITO else c
    if "1" in v.morph.get("Person"): return "eu"
    return None

def triplas(doc, por_anafora):
    out = []
    for a in doc:
        if not eh_ia(a, por_anafora): continue
        v = verbo_de(a)
        if v.pos_ not in ("VERB", "AUX") and not any(c.dep_ == "cop" for c in v.children):
            continue   # frase sem verbo que governe a IA (a árvore parou num substantivo)
        antes = [t.lower_ for t in doc[max(0, a.i - 3):a.i]]
        papel = next((PREP[p] for p in reversed(antes) if p in PREP), None)
        if papel == "com":
            papel = "parceria" if "junto" in antes or lema_v(v) in VERBOS_TROCA else "recipiente"
        if papel is None and any(c.dep_ == "cop" for c in v.children) and a.dep_.startswith("nsubj"):
            out.append(dict(tipo="IA é", verbo="ser", atributo=v.lemma_.lower(), negada=negado(v), ia=a.text)); continue
        # "peço pra ele fazer": o pedido é do verbo de cima; a IA é quem faz o infinitivo
        if papel == "destinatário" and "Inf" in v.morph.get("VerbForm") and v.head != v:
            out.append(dict(tipo="IA age", verbo=lema_v(v), atributo="", negada=negado(v), ia=a.text))
            v = v.head
        if papel is None:
            papel = "sujeito" if a.dep_.startswith("nsubj") and a.i < v.i else "objeto"
        if papel == "sujeito":
            eu_obj = any(c.lower_ in EU_OBJETO for c in v.children) or any(c.lower_ in EU_OBJETO for c in v.subtree if c.head == v)
            out.append(dict(tipo="IA → eu" if eu_obj else "IA age", verbo=lema_v(v), atributo="", negada=negado(v), ia=a.text))
        else:
            s = sujeito(v)
            if s != "eu": continue   # outra pessoa agindo sobre a IA: fica fora desta rede (só falante × IA)
            tipo = {"parceria": "eu com IA", "destinatário": "eu → IA (pra/pro)"}.get(papel, "eu → IA")
            out.append(dict(tipo=tipo, verbo=lema_v(v), atributo="", negada=negado(v), ia=a.text))
    return out

def rotulo_auto(ts):
    """Polo pela estrutura: a IA agindo (sem negação) ou parceira = alguém; o falante agindo sobre a IA, a IA negada
    como agente ou 'a IA não é X' = coisa. Sem tripla = sem rótulo."""
    if any(t["tipo"] in ("IA → eu", "IA age", "eu com IA") and not t["negada"] for t in ts): return "alguém"
    if ts: return "coisa"
    return None

def kappa(pares):
    n = len(pares)
    if not n: return float("nan")
    po = sum(a == b for a, b in pares) / n
    ca, cb = Counter(a for a, _ in pares), Counter(b for _, b in pares)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe)

def desenhar(arestas, path, n_frases, n_triplas, minimo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Liberation Sans"
    fig, ax = plt.subplots(figsize=(14, 11), dpi=200)
    fig.patch.set_facecolor(SUPERFICIE); ax.set_facecolor(SUPERFICIE); ax.axis("off")
    EU, IA = (0.0, 0.0), (10.0, 0.0)
    cor = {"eu → IA": CORES[0], "eu → IA (pra/pro)": CORES[0], "eu com IA": CORES[2], "IA → eu": CORES[1],
           "IA age": CORES[1], "IA é": TEXTO_2}
    # faixas (x, y do primeiro verbo, máximo de verbos): entre os atores, eu → IA em cima, com IA no meio e
    # IA → eu embaixo; à direita da IA, o que ela faz e o que ela é
    faixas = {"eu → IA": (5.0, 11.2, 9), "eu → IA (pra/pro)": (5.0, 4.6, 6), "eu com IA": (5.0, 0.4, 5),
              "IA → eu": (5.0, -3.8, 5), "IA age": (15.0, 11.2, 12), "IA é": (15.0, 2.2, 7)}
    passo = 0.62
    wmax = max(e["n"] for e in arestas)
    largura = lambda n: 0.8 + 5.5 * math.sqrt(n / wmax)
    for tipo, (x, topo, maximo) in faixas.items():
        es = sorted((e for e in arestas if e["tipo"] == tipo and e["n"] >= minimo), key=lambda e: -e["n"])[:maximo]
        if not es: continue
        ys = [topo - i * passo for i in range(len(es))]
        y1 = topo
        for e, y in zip(es, ys):
            ls = (0, (3, 2)) if e["neg"] == e["n"] else "-"
            alvo = (x, y)
            if tipo in ("eu → IA", "eu → IA (pra/pro)", "eu com IA"): ligs = [(EU, alvo), (alvo, IA)]
            elif tipo == "IA → eu": ligs = [(IA, alvo), (alvo, EU)]
            else: ligs = [(IA, alvo)]
            for (x0, y0_), (x1, y1_) in ligs:
                ax.annotate("", xy=(x1, y1_), xytext=(x0, y0_), zorder=1,
                            arrowprops=dict(arrowstyle="-|>", color=cor[tipo], lw=largura(e["n"]) * 0.5, alpha=0.55,
                                            linestyle=ls, shrinkA=14, shrinkB=10, mutation_scale=9))
            rot = (e["atributo"] if tipo == "IA é" else e["verbo"])
            neg = f", {e['neg']} com 'não'" if e["neg"] else ""
            ax.text(x, y, f"{rot}  {e['n']}{neg}", ha="center", va="center", fontsize=8.6, color=TEXTO, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.25", fc=SUPERFICIE, ec=cor[tipo], lw=0.9))
        rot_faixa = {"eu → IA": "eu ajo sobre a IA", "eu → IA (pra/pro)": "eu me dirijo à IA (pra/pro)",
                     "eu com IA": "eu com a IA", "IA → eu": "a IA age sobre mim", "IA age": "a IA age",
                     "IA é": "a IA é / não é"}[tipo]
        ax.text(x, y1 + 0.45, rot_faixa, ha="center", va="bottom", fontsize=9.5, color=cor[tipo], fontweight="semibold",
                zorder=3, bbox=dict(boxstyle="square,pad=0.1", fc=SUPERFICIE, ec="none"))
    for (x, y), nome in ((EU, "eu"), (IA, "IA")):
        ax.scatter([x], [y], s=2600, color=TEXTO, zorder=4)
        ax.text(x, y, nome, ha="center", va="center", fontsize=15, color=SUPERFICIE, fontweight="semibold", zorder=5)
    ax.set_xlim(-1.5, 17.0); ax.set_ylim(-5.4, 12.3)
    fig.text(0.03, 0.975, "Quem faz o quê a quem: a rede relacional entre o falante e a IA", fontsize=15,
             fontweight="semibold", color=TEXTO, va="top")
    fig.text(0.03, 0.945, f"{n_triplas} triplas sujeito–verbo–objeto extraídas da sintaxe de {n_frases} frases que mencionam a IA "
             f"(spaCy, sem a codificação manual). Espessura = nº de frases; tracejado = sempre negado; até 12 verbos por faixa, "
             f"com ao menos {minimo} frases.", fontsize=9.2, color=TEXTO_2, va="top", wrap=True)
    fig.savefig(path, facecolor=SUPERFICIE)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codigos", default="codificacao/ia_enquadramento.csv")
    ap.add_argument("--min", type=int, default=2, help="frases mínimas para um verbo aparecer na figura")
    a = ap.parse_args()
    nlp = spacy.load("pt_core_news_md", disable=["ner"])
    mencoes = ler_csv("data/ia_mencoes.csv")
    linhas, por_frase = [], {}
    for m, doc in zip(mencoes, nlp.pipe((preparar(x["frase"]) for x in mencoes), batch_size=64)):
        ts = triplas(doc, m["gatilho"] == "anáfora")
        por_frase[m["id"]] = ts
        linhas += [dict(id=m["id"], participante=m["participante"], minuto=m["minuto"], **t, frase=m["frase"]) for t in ts]
    with open("data/ia_triplas.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)

    # arestas agregadas por tipo e verbo (ou atributo), contando frases distintas
    agg = defaultdict(lambda: {"frases": set(), "neg": set(), "pessoas": set()})
    for l in linhas:
        k = (l["tipo"], l["verbo"], l["atributo"])
        agg[k]["frases"].add(l["id"]); agg[k]["pessoas"].add(l["participante"])
        if l["negada"]: agg[k]["neg"].add(l["id"])
    arestas = [dict(tipo=t, verbo=v, atributo=at, n=len(d["frases"]), neg=len(d["neg"]), pessoas=len(d["pessoas"]))
               for (t, v, at), d in agg.items()]
    arestas.sort(key=lambda e: (TIPOS.index(e["tipo"]), -e["n"]))
    with open("figuras/ia_rede_relacional_arestas.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(arestas[0])); w.writeheader(); w.writerows(arestas)
    com_tripla = sum(bool(t) for t in por_frase.values())
    desenhar(arestas, "figuras/ia_rede_relacional.png", com_tripla, len(linhas), a.min)

    print(f"{len(linhas)} triplas em {com_tripla} das {len(mencoes)} frases; por tipo: {dict(Counter(l['tipo'] for l in linhas))}")
    for t in TIPOS:
        top = [e for e in arestas if e["tipo"] == t][:10]
        print(f"  {t}: " + ", ".join(f"{e['atributo'] or e['verbo']} {e['n']}" + (f" ({e['neg']} não)" if e["neg"] else "") for e in top))
    # comparação com a codificação manual (polos, voz própria)
    cod = {r["id"]: r for r in ler_csv(a.codigos, "utf-8")}
    pares, sem = [], Counter()
    for i, ts in por_frase.items():
        c = cod.get(i)
        if not c or c["codigo"] not in POLO or c["proprio"] != "1": continue
        auto = rotulo_auto(ts)
        if auto is None: sem[POLO[c["codigo"]]] += 1; continue
        pares.append((POLO[c["codigo"]], auto))
    cm = Counter(pares)
    print(f"comparação com a codificação manual: {len(pares)} frases com rótulo automático; sem tripla: {dict(sem)}")
    print(f"  manual alguém → auto alguém {cm[('alguém', 'alguém')]}, auto coisa {cm[('alguém', 'coisa')]}; "
          f"manual coisa → auto alguém {cm[('coisa', 'alguém')]}, auto coisa {cm[('coisa', 'coisa')]}; "
          f"concordância {sum(a == b for a, b in pares) / len(pares):.0%}, kappa {kappa(pares):.2f}")
    print("figura: figuras/ia_rede_relacional.png")

if __name__ == "__main__":
    main()
