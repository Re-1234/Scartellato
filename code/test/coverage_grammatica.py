import re
from lark import Tree


def estrai_mappa_regole(percorso_grammatica: str) -> dict[str, str]:
    """Mappa ogni possibile Tree.data (nome regola o alias '-> x') alla regola
    grammaticale che lo dichiara. Copre sia regole con alias su ogni ramo,
    sia regole senza alias (Tree.data == nome della regola stessa)."""
    with open(percorso_grammatica, encoding="utf-8") as f:
        contenuto = f.read()
    contenuto_pulito = re.sub(r'//.*', '', contenuto)
    contenuto_pulito = re.sub(r'/\*[\s\S]*?\*/', '', contenuto_pulito)

    # spezza il file in blocchi "nome_regola: corpo" fino alla prossima
    # definizione di regola in colonna 0 (euristica: riga che inizia con
    # [?!]?nome_regola seguito da ':')
    pattern_def = re.compile(
        r'^\s*[?!]?([a-z_][a-zA-Z0-9_]*)\s*(?:\[.*\])?\s*:',
        re.MULTILINE
    )

    matches = list(pattern_def.finditer(contenuto_pulito))
    mappa: dict[str, str] = {}

    for i, m in enumerate(matches):
        nome_regola = m.group(1)
        if nome_regola.startswith('_'):
            continue

        inizio_corpo = m.end()
        fine_corpo = matches[i + 1].start() if i + 1 < len(matches) else len(contenuto_pulito)
        corpo = contenuto_pulito[inizio_corpo:fine_corpo]

        # la regola stessa è sempre un possibile Tree.data
        # (per i rami senza alias esplicito su quel ramo)
        mappa[nome_regola] = nome_regola

        # ogni ramo separato da "|" può avere il proprio "-> alias"
        for ramo in corpo.split('|'):
            alias_match = re.search(r'->\s*([a-zA-Z_][a-zA-Z0-9_]*)', ramo)
            if alias_match:
                mappa[alias_match.group(1)] = nome_regola

    return mappa


def estrai_regole_osservabili(percorso_grammatica: str) -> set[str]:
    """Nomi di regola 'di alto livello' (esclude quelle prefissate con '_').
    Una regola è considerata coperta se compare lei stessa O uno dei suoi alias."""
    mappa = estrai_mappa_regole(percorso_grammatica)
    return set(mappa.values())


def raccogli_regole_usate(tree, mappa: dict[str, str], accumulatore: set[str] | None = None) -> set[str]:
    if accumulatore is None:
        accumulatore = set()
    if isinstance(tree, Tree):
        regola_sorgente = mappa.get(tree.data, tree.data)
        accumulatore.add(regola_sorgente)
        for figlio in tree.children:
            raccogli_regole_usate(figlio, mappa, accumulatore)
    return accumulatore


REGOLE_COPERTE_GLOBALI: set[str] = set()


def stampa_coverage_grammatica(percorso_grammatica: str):
    mappa = estrai_mappa_regole(percorso_grammatica)
    tutte = estrai_regole_osservabili(percorso_grammatica)
    coperte = REGOLE_COPERTE_GLOBALI & tutte
    non_coperte = tutte - coperte
    percentuale = 100 * len(coperte) / len(tutte) if tutte else 0

    print(f"\n===== COVERAGE GRAMMATICA =====")
    print(f"Regole totali osservabili: {len(tutte)}")
    print(f"Regole coperte dai test: {len(coperte)} ({percentuale:.1f}%)")
    if non_coperte:
        print("Regole MAI esercitate dai test case:")
        for r in sorted(non_coperte):
            print(f"  - {r}")
    return percentuale