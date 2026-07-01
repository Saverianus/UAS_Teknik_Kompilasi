# Tugas Proyek Akhir — Representasi Tahapan Kompilasi

**Nama:** Saverianus Yolga
**NIM:** 221011403257
**Mata Kuliah:** Teknik Kompilasi
**Program Studi:** Teknik Informatika, Universitas Pamulang

---

## 1. Pilihan Konstruksi

Konstruksi sintaksis yang dipilih adalah **Perulangan (Looping) — `for`**.

Bentuk umum yang diimplementasikan:

```
for ( int i = 0 ; i < 5 ; i++ ) {
    kuadrat = i * i;
}
```

Konstruksi ini dipilih karena `for` loop melibatkan tiga komponen sekaligus (inisialisasi, kondisi, increment) yang menarik untuk direpresentasikan pada setiap tahapan kompilasi, terutama saat menghasilkan *Three-Address Code* dengan label lompatan (`goto`) untuk membentuk struktur perulangan.

## 2. Pattern (Pola Sintaks — BNF)

Grammar didefinisikan menggunakan pendekatan *Backus-Naur Form* (BNF) sederhana:

```
<for_stmt>       ::= "for" "(" <init> ";" <condition> ";" <increment> ")"
                     "{" <statement_list> "}"

<init>           ::= ["int"] <identifier> "=" <value>

<condition>      ::= <identifier> <relop> <value>

<increment>      ::= <identifier> "++" | <identifier> "--"

<statement_list> ::= <statement> { <statement> }

<statement>      ::= <identifier> "=" <expression> ";"

<expression>     ::= <identifier> [ <addop> <value> ]

<relop>          ::= "==" | "!=" | "<" | ">" | "<=" | ">="

<addop>          ::= "+" | "-" | "*" | "/"

<value>          ::= <number> | <identifier>
```

## 3. Implementasi Program

Implementasi dibuat menggunakan **Python 3** pada file [`for_loop_compiler.py`](for_loop_compiler.py), yang merepresentasikan empat tahapan kompilasi berikut secara berurutan.

### 3.1 Tahap Analisis Leksikal (Lexical Analysis)

Fungsi `lexical_analysis()` memecah *source code* menjadi deretan token menggunakan *Regular Expression* (modul `re`). Setiap token memiliki `type` (kategori) dan `value` (nilai literalnya).

Kategori token yang dikenali:

| Jenis Token | Contoh |
|---|---|
| `FOR` | `for` |
| `INT` | `int` |
| `ID` (identifier) | `i`, `kuadrat` |
| `NUMBER` | `0`, `5` |
| `OP` (operator) | `=`, `<`, `++`, `*` |
| `LPAREN` / `RPAREN` | `(` `)` |
| `LBRACE` / `RBRACE` | `{` `}` |
| `SEMI` | `;` |

Contoh hasil tokenisasi dari `for ( int i = 0 ; i < 5 ; i++ ) { kuadrat = i * i; }`:

```
Token(FOR, 'for')
Token(LPAREN, '(')
Token(INT, 'int')
Token(ID, 'i')
Token(OP, '=')
Token(NUMBER, '0')
Token(SEMI, ';')
...
```

### 3.2 Tahap Analisis Sintaksis (Syntax Analysis) — AST

Kelas `Parser` mengimplementasikan *recursive-descent parser* yang mengonsumsi token satu per satu (`eat()`) sesuai urutan grammar BNF di atas, lalu membentuk **Abstract Syntax Tree (AST)** berupa struktur `dict` bersarang dengan node:

- `ForStatement` (node akar, memiliki `init`, `condition`, `increment`, `body`)
- `Assign` (penugasan nilai ke variabel)
- `Condition` (ekspresi kondisi perulangan)
- `IncDec` (operasi `++` / `--`)
- `BinOp` (operasi biner seperti `i * i`)
- `Identifier` / `Literal` (operand)

Potongan AST yang dihasilkan (format JSON):

```json
{
  "type": "ForStatement",
  "init": {"type": "Assign", "target": "i", "value": {"type": "Literal", "value": "0"}},
  "condition": {"type": "Condition", "left": "i", "operator": "<", "right": {"type": "Literal", "value": "5"}},
  "increment": {"type": "IncDec", "target": "i", "operator": "++"},
  "body": [
    {"type": "Assign", "target": "kuadrat",
     "value": {"type": "BinOp", "operator": "*",
               "left": {"type": "Identifier", "name": "i"},
               "right": {"type": "Identifier", "name": "i"}}}
  ]
}
```

Jika token tidak sesuai urutan grammar (misalnya kurung tidak ditutup), parser akan melempar `SyntaxError` — ini mensimulasikan tahap deteksi kesalahan sintaksis pada kompiler sungguhan.

### 3.3 Tahap Analisis Semantik (Semantic Analysis)

Fungsi `semantic_analysis()` melakukan pengecekan dasar terhadap AST menggunakan *symbol table* (`dict` Python):

1. Variabel pada `init` (misalnya `i`) otomatis didaftarkan ke *symbol table* dengan tipe `int`.
2. Setiap identifier yang muncul di `condition`, `increment`, maupun `body` divalidasi — jika belum pernah dideklarasikan/di-assign sebelumnya, program akan melempar `SemanticError`.
3. Variabel baru yang muncul sebagai *target* penugasan di dalam `body` (misalnya `kuadrat`) otomatis didaftarkan ke *symbol table*.

Contoh kasus **valid**:

```
i : int
kuadrat : int
Status: Valid, tidak ditemukan kesalahan semantik.
```

Contoh kasus **tidak valid** (variabel `y` dipakai tapi tidak pernah dideklarasikan):

```python
for ( int i = 0 ; i < 3 ; i++ ) {
    x = y + 1;
}
```

Hasil: `SemanticError: Variabel 'y' digunakan sebelum dideklarasikan.`

### 3.4 Tahap Generasi Kode Antara (Three-Address Code)

Kelas `TACGenerator` menelusuri AST (mirip *tree traversal* pada kompiler nyata) dan menghasilkan **Three-Address Code (TAC)** dengan:

- Variabel sementara (`t1`, `t2`, …) untuk menampung hasil sub-ekspresi (`gen_expr()`), sehingga setiap instruksi TAC maksimal memiliki satu operator (*three-address* property).
- Label (`L1`, `L2`, …) untuk menandai awal dan akhir perulangan.
- Instruksi `ifFalse (...) goto ...` untuk mensimulasikan percabangan bersyarat yang keluar dari loop ketika kondisi bernilai salah.
- Instruksi `goto` untuk kembali ke awal loop setelah bagian *increment* dieksekusi — inilah yang membuat struktur *for* menjadi sebuah *loop* pada level kode antara.

Hasil akhir TAC untuk contoh program:

```
i = 0
L1:
ifFalse (i < 5) goto L2
t1 = i * i
kuadrat = t1
i = i + 1
goto L1
L2:
```

Penjelasan alur TAC di atas:

1. `i = 0` — inisialisasi variabel loop.
2. `L1:` — label awal iterasi.
3. `ifFalse (i < 5) goto L2` — jika kondisi salah, lompat ke `L2` (keluar loop).
4. `t1 = i * i` dan `kuadrat = t1` — badan perulangan (dipecah menjadi *temporary variable* sesuai aturan *three-address code*).
5. `i = i + 1` — increment.
6. `goto L1` — kembali ke awal loop.
7. `L2:` — label akhir/keluar loop.

## 4. Cara Menjalankan Program

```bash
python3 for_loop_compiler.py
```

Program akan menampilkan keempat tahapan secara berurutan: token hasil lexical analysis, AST hasil syntax analysis, symbol table hasil semantic analysis, dan Three-Address Code hasil generasi kode antara.

Contoh input dapat diubah pada variabel `contoh_source` di bagian akhir file (`if __name__ == "__main__":`).

## 5. Struktur Repositori

```
.
├── for_loop_compiler.py   # Implementasi lengkap 4 tahapan kompilasi
├── DOKUMENTASI.md          # Dokumen penjelasan ini
└── README.md               # Ringkasan proyek
```

## 6. Kesimpulan

Program ini berhasil mensimulasikan empat tahapan utama kompilasi untuk konstruksi `for` loop, mulai dari pemecahan token, pembentukan AST, validasi semantik sederhana (deteksi variabel yang belum dideklarasikan), hingga menghasilkan Three-Address Code yang merepresentasikan struktur perulangan menggunakan label dan instruksi lompat (`goto`).
