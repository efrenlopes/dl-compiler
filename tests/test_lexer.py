from dlc.lex.tag import Tag
from dlc.lex.lexer import Lexer
from io import StringIO

source_code = '''
programa area_circulo inicio
  real raio;
  booleano positivo;
  raio = 5;
  positivo = (raio > 1 | raio == 1);
  se (positivo == verdade) inicio
    real area;
    area = 3.1415 * raio * raio;
    escreva(area);
  fim;
fim.
'''

tags_seq = (Tag.PROGRAM, Tag.ID, Tag.BEGIN,
            Tag.REAL, Tag.ID, Tag.SEMI,
            Tag.BOOL, Tag.ID, Tag.SEMI,
            Tag.ID, Tag.ASSIGN, Tag.LIT_INT, Tag.SEMI,
            Tag.ID, Tag.ASSIGN, Tag.LPAREN, Tag.ID, Tag.GT, Tag.LIT_INT, Tag.OR, Tag.ID, Tag.EQ, Tag.LIT_INT, Tag.RPAREN, Tag.SEMI,
            Tag.IF, Tag.LPAREN, Tag.ID, Tag.EQ, Tag.LIT_TRUE, Tag.RPAREN, Tag.BEGIN,
            Tag.REAL, Tag.ID, Tag.SEMI,
            Tag.ID, Tag.ASSIGN, Tag.LIT_REAL, Tag.MUL, Tag.ID, Tag.MUL, Tag.ID, Tag.SEMI,
            Tag.WRITE, Tag.LPAREN, Tag.ID, Tag.RPAREN, Tag.SEMI,
            Tag.END, Tag.SEMI,
            Tag.END, Tag.DOT)

def test_lexer():
    lexer = Lexer(StringIO(source_code))
    token = lexer.next_token()
    i = 0
    while i < len(tags_seq) and token.tag != Tag.EOF:
        assert token.tag == tags_seq[i], f'Erro no token {i}: esperado "{tags_seq[i].name}", recebido "{token.tag.name}"'
        token = lexer.next_token()
        i += 1
    assert token.tag == Tag.EOF
