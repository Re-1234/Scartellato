import re
from lark import Tree


def estrai_regole_osservabili(percorso_grammatica: str) -> set[str]:
    """Regole della grammatica .lark che possono comparire come Tree.data
    (esclude quelle prefissate con '_', che Lark 'inlinea' nel genitore)."""
    con_regex = re.compile(r'^\s*[?!]?([a-z_][a-zA-Z0-9_]*)\s*(\[.*\])?\s*:', re.MULTILINE)

    with open(percorso_grammatica, encoding="utf-8") as f:
        contenuto = f.read()
    contenuto_pulito = re.sub(r'//.*', '', contenuto)

    tutte = {m.group(1) for m in con_regex.finditer(contenuto_pulito)}
    return {r for r in tutte if not r.startswith('_')}


def raccogli_regole_usate(tree, accumulatore: set[str] | None = None) -> set[str]:
    if accumulatore is None:
        accumulatore = set()
    if isinstance(tree, Tree):
        accumulatore.add(tree.data)
        for figlio in tree.children:
            raccogli_regole_usate(figlio, accumulatore)
    return accumulatore


REGOLE_COPERTE_GLOBALI: set[str] = set()


def stampa_coverage_grammatica(percorso_grammatica: str):
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