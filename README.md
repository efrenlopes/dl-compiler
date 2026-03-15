# ⚙️ DL Compiler (DLC)

Compilador da **DL (Didactic Language)** desenvolvido para a disciplina de **Compiladores** da **Universidade Federal do Oeste do Pará (UFOPA)**.

O projeto implementa um compilador completo para a linguagem DL, incluindo:

- Análise léxica
- Análise sintática
- Análise semântica
- Geração de **IR (Intermediate Representation)**
- Transformação para **SSA (Static Single Assignment)**
- Otimizações
- Alocação de registradores
- Geração de código **x86-64**




## 📂 Estrutura do Projeto

```
src/dlc
├── codegen     # Geração de código e alocação de registradores
├── inter       # Representação intermediária (IR) e SSA
├── lex         # Análise léxica
├── semantic    # Análise semântica e sistema de tipos
├── syntax      # Parser
└── tree        # Estrutura da AST
```

## 🛠️ Pré-requisitos

- Python **3.12**
- uv **0.10.9**





## 🚀 Configuração e execução


Após clonar o repositório, para criar automaticamente o ambiente virtual e instalar as dependências, execute

```bash
uv sync
```

Para executar o compilador utilizando como entrada um programa-fonte faça
```bash
uv run python -m dlc tests/inputs/prog.dl
```



## 💻 Configuração no VSCode

O repositório já inclui arquivos de configuração para execução no **VSCode**, então basta
1. Abrir o projeto no VSCode;
2. Selecionar como *interpreter* `.venv/bin/python`



## 📝 Gramática da linguagem DL
```bnf
<PROGRAM>   ::= "programa" ID <STMT> "."
<STMT>	    ::= <BLOCK> | <DECL> | <ASSIGN> | <WRITE> | <IF> | <WHILE>
<DECL>      ::= TYPE ID <DECL_REST>
<DECL_REST> ::= "," ID <DECL_REST> | ε
<BLOCK>     ::= "inicio" <STMTS> "fim"
<STMTS>     ::= <STMT> ";" <STMTS> | ε
<ASSIGN>    ::= ID "=" <EXPR>
<IF>        ::= "se" "(" <EXPR> ")" <STMT>
<ELSE>      ::= "se" "(" <EXPR> ")" <STMT> "senao" <STMT>
<WHILE>     ::= "enquanto" "(" <EXPR> ")" <STMT>
<WRITE>     ::= "escreva" "(" <EXPR> ")"
<READ>      ::= "leia" "(" ID ")"
<EXPR>      ::= <EXPR> "|" <LAND> | <LAND>
<LAND>      ::= <LAND> "&" <EQUAL> | <EQUAL>
<EQUAL>     ::= <EQUAL> EQ_OP <REL> | <REL>
<REL>       ::= <REL> REL_OP <ARITH> | <ARITH>
<ARITH>     ::= <ARITH> "+" <TERM> | <ARITH> "-" <TERM> | <TERM>
<TERM>      ::= <TERM> "*" <UNARY> | <TERM> "/" <UNARY> | <TERM> "%" <UNARY> | <UNARY>
<UNARY>     ::= "+" <UNARY> | "-" <UNARY> | "!" <UNARY> | <POW>
<POW>		::= <FACTOR> "^" <UNARY> | <FACTOR>
<FACTOR>    ::= "(" <EXPR> ")" | ID | LIT_INT | LIT_REAL | LIT_BOOL

LETTER      = "a" | "b" | ... | "z" | "A" | "B" | ... "Z" | "_"
DIGIT       = "0" | "1" | ... | "9"
ID          = LETTER (LETTER | DIGIT)*
LIT_INT     = DIGIT+
LIT_REAL    = DIGIT+ "." DIGIT* 
LIT_BOOL    = "verdade" | "falso"
TYPE        = "inteiro" | "real" | "booleano"
EQ_OP       = "==" | "!="
REL_OP      = "<" | "<=" | ">" | ">="
```