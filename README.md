## Para rodar o projeto, entre na pasta do projeto e rode
```bash
PYTHONPATH=src python -m dl ./test/prog.dl
```


## Gramática Projeto completo da linguagem DL
```bnf
<PROGRAM>   ::= "programa" ID <STMT> "."
<STMT>	    ::= <BLOCK> | <DECL> | <ASSIGN> | <WRITE> | <IF>
<BLOCK>     ::= "inicio" <STMTS> "fim"
<STMTS>     ::= <STMT> ";" <STMTS> | ε
<DECL>      ::= TYPE ID
<ASSIGN>    ::= ID "=" <EXPR>
<WRITE>     ::= "escreva" "(" <EXPR> ")"
<IF>        ::= "se" "(" <EXPR> ")" <STMT>
<EXPR>      ::= <EXPR> "|" <EQUAL> | <EQUAL>
<EQUAL>     ::= <EQUAL> "==" <REL> | <REL>
<REL>       ::= <REL> "<" <ARITH> | <REL> ">" <ARITH> | <ARITH>
<ARITH>     ::= <ARITH> "+" <TERM> | <ARITH> "-" <TERM> | <TERM>
<TERM>      ::= <TERM> "*" <FACTOR>
<FACTOR>    ::= "(" <EXPR> ")" | ID | LIT_INT | LIT_REAL | LIT_BOOL

LETTER      = "a" | "b" | ... | "z" | "A" | "B" | ... "Z" | "_"
DIGIT       = "0" | "1" | ... | "9"
ID          = LETTER (LETTER | DIGIT)*
LIT_INT     = DIGIT+
LIT_REAL    = DIGIT+ "." DIGIT* 
LIT_BOOL    = "verdade" | "falso"
TYPE        = "inteiro" | "real" | "booleano"
```