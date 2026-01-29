## Para rodar o projeto, entre na pasta do projeto e rode
```bash
PYTHONPATH=src python -m dl tests/inputs/prog.dl
```


## Gramática Projeto completo da linguagem DL
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
<TERM>      ::= <TERM> "*" <FACTOR> | <TERM> "/" <FACTOR> | <TERM> "%" <FACTOR> | <FACTOR>
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