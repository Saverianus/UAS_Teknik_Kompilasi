"""
Tugas Proyek Akhir - Teknik Kompilasi
Representasi Tahapan Kompilasi untuk Konstruksi: Perulangan (For Loop)

Konstruksi yang dipilih : for ( init ; condition ; increment ) { statements }
Tahapan yang disimulasikan:
    1. Analisis Leksikal   -> memecah source code menjadi token
    2. Analisis Sintaksis  -> membentuk Abstract Syntax Tree (AST)
    3. Analisis Semantik   -> validasi deklarasi variabel & tipe data sederhana
    4. Generasi Kode Antara -> menghasilkan Three-Address Code (TAC)

Author  : Saverianus Yolga (221011403257)
Mata Kuliah : Teknik Kompilasi
"""

import re


# =========================================================
# 1. ANALISIS LEKSIKAL (LEXICAL ANALYSIS)
# =========================================================

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


# Definisi pola token menggunakan Regular Expression (urutan penting!)
TOKEN_SPEC = [
    ("NUMBER",   r"\d+"),
    ("FOR",      r"\bfor\b"),
    ("INT",      r"\bint\b"),
    ("ID",       r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("OP",       r"==|!=|<=|>=|\+\+|--|[+\-*/=<>]"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("LBRACE",   r"\{"),
    ("RBRACE",   r"\}"),
    ("SEMI",     r";"),
    ("SKIP",     r"[ \t\n]+"),
]

MASTER_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


def lexical_analysis(source_code: str):
    """Memecah source code menjadi daftar token (tahap Analisis Leksikal)."""
    tokens = []
    pos = 0
    while pos < len(source_code):
        match = MASTER_REGEX.match(source_code, pos)
        if not match:
            raise SyntaxError(f"Karakter tidak dikenali pada posisi {pos}: {source_code[pos]!r}")
        kind = match.lastgroup
        value = match.group()
        pos = match.end()
        if kind == "SKIP":
            continue
        tokens.append(Token(kind, value))
    tokens.append(Token("EOF", None))
    return tokens


# =========================================================
# 2. ANALISIS SINTAKSIS (SYNTAX ANALYSIS) -> AST
# =========================================================

# Node-node AST direpresentasikan sebagai dictionary sederhana agar mudah dibaca

class Parser:
    """
    Grammar (BNF) yang diimplementasikan:

    <for_stmt>   ::= "for" "(" <init> ";" <condition> ";" <increment> ")"
                     "{" <statement_list> "}"
    <init>       ::= ["int"] <identifier> "=" <value>
    <condition>  ::= <identifier> <relop> <value>
    <increment>  ::= <identifier> "++" | <identifier> "--" | <identifier> "=" <identifier> <addop> <value>
    <statement_list> ::= <statement> { <statement> }
    <statement>  ::= <identifier> "=" <expression> ";"
    <expression> ::= <identifier> [ <addop> <value> ]
    <relop>      ::= "==" | "!=" | "<" | ">" | "<=" | ">="
    <addop>      ::= "+" | "-" | "*" | "/"
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, expected_type=None):
        tok = self.current()
        if expected_type and tok.type != expected_type:
            raise SyntaxError(f"Diharapkan token {expected_type}, tetapi ditemukan {tok.type} ({tok.value!r})")
        self.pos += 1
        return tok

    def parse_for_statement(self):
        self.eat("FOR")
        self.eat("LPAREN")
        init_node = self.parse_init()
        self.eat("SEMI")
        cond_node = self.parse_condition()
        self.eat("SEMI")
        incr_node = self.parse_increment()
        self.eat("RPAREN")
        self.eat("LBRACE")
        body_nodes = self.parse_statement_list()
        self.eat("RBRACE")

        return {
            "type": "ForStatement",
            "init": init_node,
            "condition": cond_node,
            "increment": incr_node,
            "body": body_nodes,
        }

    def parse_init(self):
        if self.current().type == "INT":
            self.eat("INT")
        ident = self.eat("ID").value
        self.eat("OP")  # '='
        value = self.eat("NUMBER").value
        return {"type": "Assign", "target": ident, "value": {"type": "Literal", "value": value}}

    def parse_condition(self):
        left = self.eat("ID").value
        op = self.eat("OP").value
        right_tok = self.current()
        if right_tok.type == "NUMBER":
            right = {"type": "Literal", "value": self.eat("NUMBER").value}
        else:
            right = {"type": "Identifier", "name": self.eat("ID").value}
        return {"type": "Condition", "left": left, "operator": op, "right": right}

    def parse_increment(self):
        ident = self.eat("ID").value
        op_tok = self.eat("OP")
        if op_tok.value in ("++", "--"):
            return {"type": "IncDec", "target": ident, "operator": op_tok.value}
        # bentuk: x = x + 1
        raise SyntaxError("Bentuk increment tidak didukung, gunakan '++' atau '--'.")

    def parse_statement_list(self):
        statements = []
        while self.current().type != "RBRACE":
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        ident = self.eat("ID").value
        self.eat("OP")  # '='
        expr = self.parse_expression()
        self.eat("SEMI")
        return {"type": "Assign", "target": ident, "value": expr}

    def parse_expression(self):
        left_tok = self.current()
        if left_tok.type == "NUMBER":
            left = {"type": "Literal", "value": self.eat("NUMBER").value}
        else:
            left = {"type": "Identifier", "name": self.eat("ID").value}

        if self.current().type == "OP" and self.current().value in ("+", "-", "*", "/"):
            op = self.eat("OP").value
            right_tok = self.current()
            if right_tok.type == "NUMBER":
                right = {"type": "Literal", "value": self.eat("NUMBER").value}
            else:
                right = {"type": "Identifier", "name": self.eat("ID").value}
            return {"type": "BinOp", "operator": op, "left": left, "right": right}

        return left


def syntax_analysis(tokens):
    """Membentuk Abstract Syntax Tree (AST) dari daftar token (tahap Analisis Sintaksis)."""
    parser = Parser(tokens)
    ast = parser.parse_for_statement()
    return ast


# =========================================================
# 3. ANALISIS SEMANTIK (SEMANTIC ANALYSIS)
# =========================================================

class SemanticError(Exception):
    pass


def semantic_analysis(ast):
    """
    Melakukan pengecekan dasar:
      - Variabel yang dipakai pada condition/increment/body harus sudah dideklarasikan (via init).
      - Tipe data disederhanakan: semua variabel bertipe 'int'.
    Mengembalikan symbol table jika valid.
    """
    symbol_table = {}

    # Variabel dari init otomatis terdeklarasi
    init_var = ast["init"]["target"]
    symbol_table[init_var] = "int"

    def check_identifier(name):
        if name not in symbol_table:
            raise SemanticError(f"Variabel '{name}' digunakan sebelum dideklarasikan.")

    # Cek condition
    if ast["condition"]["left"] not in symbol_table:
        raise SemanticError(f"Variabel '{ast['condition']['left']}' pada kondisi belum dideklarasikan.")
    if ast["condition"]["right"]["type"] == "Identifier":
        check_identifier(ast["condition"]["right"]["name"])

    # Cek increment
    if ast["increment"]["target"] not in symbol_table:
        raise SemanticError(f"Variabel '{ast['increment']['target']}' pada increment belum dideklarasikan.")

    # Cek body: setiap assignment mendaftarkan variabel baru (jika belum ada) & memvalidasi operand
    for stmt in ast["body"]:
        target = stmt["target"]
        value = stmt["value"]

        if value["type"] == "Identifier":
            check_identifier(value["name"])
        elif value["type"] == "BinOp":
            for side in (value["left"], value["right"]):
                if side["type"] == "Identifier":
                    check_identifier(side["name"])

        # Deklarasikan variabel target jika belum ada (implicit declaration hasil assignment)
        symbol_table.setdefault(target, "int")

    return symbol_table


# =========================================================
# 4. GENERASI KODE ANTARA (THREE-ADDRESS CODE)
# =========================================================

class TACGenerator:
    def __init__(self):
        self.temp_counter = 1
        self.label_counter = 1
        self.code = []

    def new_temp(self):
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def new_label(self):
        l = f"L{self.label_counter}"
        self.label_counter += 1
        return l

    def emit(self, instruction):
        self.code.append(instruction)

    def gen_expr(self, node):
        """Menghasilkan TAC untuk sebuah ekspresi, mengembalikan nama variabel/temp hasil."""
        if node["type"] == "Literal":
            return node["value"]
        if node["type"] == "Identifier":
            return node["name"]
        if node["type"] == "BinOp":
            left = self.gen_expr(node["left"])
            right = self.gen_expr(node["right"])
            temp = self.new_temp()
            self.emit(f"{temp} = {left} {node['operator']} {right}")
            return temp
        raise ValueError(f"Node ekspresi tidak dikenali: {node}")

    def generate(self, ast):
        # 1) Inisialisasi
        init = ast["init"]
        init_val = self.gen_expr(init["value"])
        self.emit(f"{init['target']} = {init_val}")

        label_start = self.new_label()
        label_end = self.new_label()

        # 2) Label mulai loop
        self.emit(f"{label_start}:")

        # 3) Evaluasi kondisi -> lompat keluar jika salah
        cond = ast["condition"]
        right_val = self.gen_expr(cond["right"])
        self.emit(f"ifFalse ({cond['left']} {cond['operator']} {right_val}) goto {label_end}")

        # 4) Badan perulangan
        for stmt in ast["body"]:
            val = self.gen_expr(stmt["value"])
            self.emit(f"{stmt['target']} = {val}")

        # 5) Increment
        incr = ast["increment"]
        if incr["operator"] == "++":
            self.emit(f"{incr['target']} = {incr['target']} + 1")
        else:  # '--'
            self.emit(f"{incr['target']} = {incr['target']} - 1")

        # 6) Lompat kembali ke label mulai
        self.emit(f"goto {label_start}")

        # 7) Label akhir
        self.emit(f"{label_end}:")

        return self.code


def generate_tac(ast):
    generator = TACGenerator()
    return generator.generate(ast)


# =========================================================
# PROGRAM UTAMA (DRIVER)
# =========================================================

def compile_for_loop(source_code: str):
    print("=" * 60)
    print("SOURCE CODE")
    print("=" * 60)
    print(source_code.strip())

    print("\n" + "=" * 60)
    print("TAHAP 1: ANALISIS LEKSIKAL (TOKENS)")
    print("=" * 60)
    tokens = lexical_analysis(source_code)
    for tok in tokens:
        print(tok)

    print("\n" + "=" * 60)
    print("TAHAP 2: ANALISIS SINTAKSIS (ABSTRACT SYNTAX TREE)")
    print("=" * 60)
    ast = syntax_analysis(tokens)
    import json
    print(json.dumps(ast, indent=2))

    print("\n" + "=" * 60)
    print("TAHAP 3: ANALISIS SEMANTIK (SYMBOL TABLE)")
    print("=" * 60)
    symbol_table = semantic_analysis(ast)
    for var, typ in symbol_table.items():
        print(f"  {var} : {typ}")
    print("Status: Valid, tidak ditemukan kesalahan semantik.")

    print("\n" + "=" * 60)
    print("TAHAP 4: GENERASI THREE-ADDRESS CODE (TAC)")
    print("=" * 60)
    tac = generate_tac(ast)
    for line in tac:
        print(line)

    return tokens, ast, symbol_table, tac


if __name__ == "__main__":
    contoh_source = """
    for ( int i = 0 ; i < 5 ; i++ ) {
        kuadrat = i * i;
    }
    """
    compile_for_loop(contoh_source)
