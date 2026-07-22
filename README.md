# Scartellato 🤌 

> **Benvenuti repository ufficiale del linguaggio di programmazione più napoletano che esista.**

**Scartellato** è un progetto universitario creato ad Unisa nell'anno 2025/2026 nato con l'obiettivo di acquisire conoscenze sulle architetture dei linguaggi di programmazione.


## Architettura & Pipeline di Compilazione

La pipeline si articola in **3 fasi principali**:

1. **Analisi Sintattica:**
   * Definizione dei token e dei costrutti cardine del linguaggio.
   * Definizione della grammatica sintattica 
   * Generazione del *Parse Tree* e successiva trasformazione in un **AST (Abstract Syntax Tree)** nativo basato su nodi Python.

2. **Analisi Semantica:**
   * Controllo sul rispetto delle regole semantiche definite dal linguaggio.
   * Gestione corretta dello *scope*, dichiarazione e compatibilità dei tipi di dato.

3. **Transpiler verso C (Back-End):**
   * Traduzione dell'AST validato in codice sorgente **C**.
   * il progetto si occupa della fase di front-end della compilazione
   * Delegazione della compilazione adi basso livello a un compilatore molto robusto e verboso e efficiente quale il C per generare il binario finale.

---

🚀 Requisiti di Sistema

# Clona la repository
git clone https://github.com/Re-1234/Scartellato.git

### 1. Compilatore C
Per compilare e testare il codice tradotto sul proprio sistema, è necessario disporre di:
* **GCC (GNU Compiler Collection)** configurato correttamente nel `PATH` di sistema.

### 2. Dipendenze Python
Il compilatore sfrutta la libreria **Lark** per il parsing:
```bash
pip install lark

###Esecuzione Runtime
il progetto per essere avviato basta runnare il file compilatore.py e stamperà su terminale l'esito della esecuzione. 
Nel caso si voglia creare un programma , all'interno del file compilatore sostituire la stringa contenente il sorgente con il codice a vostro piacimento wajo.

###Esecuzione dei Test
Il progetto include una suite completa di test per verificare la correttezza semantica, la gestione dello scope, le funzioni e i costrutti del linguaggio.

Per eseguire tutti i test e visualizzare l'esito direttamente nel terminale, è sufficiente avviare l'apposito script: run_test_cases che mostrerà le statistiche su un numero predefinito di casi di test

