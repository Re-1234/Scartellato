def wrappa_burdell(transpiler, nodo_valore):
    tipo = transpiler.tipo_di(nodo_valore)
    valore_espr = transpiler.espr(nodo_valore)
    mappa = {
        "numr": "burdell_da_numr",
        "lota": "burdell_da_lota",
        "nbruogglio": "burdell_da_nbruogglio",
        "lettr": "burdell_da_lettr",
    }
    return f"{mappa[tipo]}({valore_espr})"

def _accesso_base(transpiler, nome):
    """Decide come accedere a 'nome': campo di classe (self./self->) o variabile normale."""
    if nome in transpiler.var_locali_shadow:
        return nome
    if transpiler.classe_corrente is not None and nome in transpiler.campi_classe:
        return f"self.{nome}" if transpiler.in_costruttore else f"self->{nome}"
    return nome

def _calcola_tipo(self, node):
    """Cerca il tipo nella symbol table, se non c'è lo deduce ricorsivamente."""
    if node is None:
        return None
    try:
        return self.tipo_di(node)
    except Exception:
        cls = node.__class__.__name__
        if cls == "Numr": return "numr"
        if cls == "Stringa": return "nbruogglio"
        if cls == "Boolean": return "lota"
        if cls == "Carattr": return "lettr"
        if cls == "OpBin":
            t_sx = self._calcola_tipo(node.left)
            t_dx = self._calcola_tipo(node.right)
            # Nel tuo linguaggio string + something = string
            if t_sx == "nbruogglio" or t_dx == "nbruogglio":
                return "nbruogglio"
            return t_sx
        return None



def _risolvi_chiamata(transpiler, node):
    """Restituisce (nome_c, lista_argomenti_c) per una CallStmt,
    aggiungendo prefisso di classe e 'self'/'&self' se la chiamata
    punta a un metodo della classe corrente."""
    nome = str(node.nome_func.nome)
    args = [transpiler.espr(a) for a in node.args]

    if transpiler.classe_corrente is not None and nome in transpiler.metodi_classe:
        nome_c = f"{transpiler.classe_corrente}_{nome}"
        self_arg = "&self" if transpiler.in_costruttore else "self"
        args = [self_arg] + args
    else:
        nome_c = nome

    return nome_c, args


def _is_burdell(self, node):
        return self.burdell_info.get(id(node), False)