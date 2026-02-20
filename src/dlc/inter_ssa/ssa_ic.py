from dlc.inter.basic_block import BasicBlock
from dlc.inter_ssa.ssa_instr import SSAInstr
from dlc.inter_ssa.ssa_operand import SSAConst, SSALabel, SSAOperand, SSATemp
from dlc.inter_ssa.ssa_operator import SSAOperator
from dlc.lex.tag import Tag
from dlc.semantic.type import Type
from dlc.tree.ast import AST
from dlc.tree.nodes import (
    Visitor,
    ProgramNode,
    BlockNode,
    DeclNode,
    AssignNode,
    IfNode,
    ElseNode,
    WhileNode,
    WriteNode,
    ReadNode,
    ConvertNode,
    VarNode,
    BinaryNode,
    UnaryNode,
    LiteralNode
)
from ctypes import c_int32, c_double


class SSA_IC(Visitor):
    
    __OP_MAP = {
        Tag.SUM: SSAOperator.SUM,
        Tag.SUB: SSAOperator.SUB,
        Tag.MUL: SSAOperator.MUL,
        Tag.DIV: SSAOperator.DIV,
        Tag.MOD: SSAOperator.MOD,
        Tag.POW: SSAOperator.POW,
        Tag.EQ : SSAOperator.EQ,
        Tag.NE : SSAOperator.NE,
        Tag.LT: SSAOperator.LT,
        Tag.LE: SSAOperator.LE,
        Tag.GT: SSAOperator.GT,
        Tag.GE: SSAOperator.GE
    }

    def __init__(self, ast: AST):
        self.__var_temp_map = {}
        self.__label_bb_map = {}
        self.__comments = {}
        self.bb_sequence = [BasicBlock()]
        ast.root.accept(self)

    def __iter__(self):
        for bb in self.bb_sequence:
            for instr in bb:
                yield instr
    

    def __bb_from_label(self, label):
        if label not in self.__label_bb_map:
            self.__label_bb_map[label] = BasicBlock()
        return self.__label_bb_map[label]



    def add_instr(self, instr: SSAInstr, comment: str=None):
        bb = self.bb_sequence[-1]
        instr_prev = bb.instructions[-1] if bb.instructions else None

        # 1. Decidir se precisamos trocar de bloco ANTES de processar a instrução
        if instr.op == SSAOperator.LABEL:
            bb_new = self.__bb_from_label(instr.result)
            # Se o bloco atual está vazio, apenas substitui (resolve o bb0 do init)
            if not bb.instructions:
                self.bb_sequence[-1] = bb_new
            else:
                # Só conecta se o bloco anterior não terminou em GOTO
                if instr_prev and instr_prev.op != SSAOperator.GOTO:
                    bb.add_successor(bb_new)
                self.bb_sequence.append(bb_new)
            bb = bb_new

        # Se a anterior foi um salto, a instrução ATUAL (não sendo label) precisa de um novo bloco
        elif instr_prev and instr_prev.op in (SSAOperator.GOTO, SSAOperator.IF, SSAOperator.IFFALSE):
            bb_new = BasicBlock()
            # Se era um IF, o bloco novo é o caminho "falso" (fall-through)
            if instr_prev.op != SSAOperator.GOTO:
                bb.add_successor(bb_new)
            self.bb_sequence.append(bb_new)
            bb = bb_new

        # 2. Agora que estamos no bloco correto, processamos a instrução
        if instr.op in (SSAOperator.GOTO, SSAOperator.IF, SSAOperator.IFFALSE):
            target_bb = self.__bb_from_label(instr.result)
            bb.add_successor(target_bb)

        bb.instructions.append(instr)
        if comment:
            self.__comments[instr] = comment




    def plot(self):
        from graphviz import Digraph
        dot = Digraph()
        dot.attr(fontname="consolas")
        for bb in self.bb_sequence:
            code = [str(i) for i in bb]
            dot.node(name=str(bb), label='\n'.join(code), shape="box", xlabel=str(bb))
            for s in bb.successors:
                dot.edge(str(bb), str(s))
            #for s in bb.predecessors:
            #    dot.edge(str(bb), str(s), color="red")
        dot.render('out/teste_fluxo', view=True) 





    def __str__(self):
        tac = []
        for bb in self.bb_sequence:
            tac.append(str(bb))
            for instr in bb:
                comment = self.__comments.get(instr)
                if comment:
                    tac.append(f'   {str(instr):<20} \t\t#{comment}')
                else:
                    tac.append(f'   {instr}')
        return '\n'.join(tac)


    def visit_program_node(self, node: ProgramNode):
        node.stmt.accept(self)
    

    def visit_block_node(self, node: BlockNode):
        for stmt in node.stmts:
            stmt.accept(self)
        
    
    def visit_decl_node(self, node: DeclNode):
        pass
        

    def visit_assign_node(self, node: AssignNode):
        arg = node.expr.accept(self)

        if (node.var.name, node.var.scope) not in self.__var_temp_map:
            temp = SSATemp(node.var.type)
            self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        
        temp = node.var.accept(self)
        comment = f'var {node.var.name} [scope={node.var.scope}]'
        self.add_instr(SSAInstr(SSAOperator.MOVE, arg, SSAOperand.EMPTY, temp), comment)


    def visit_var_node(self, node: VarNode):
        return self.__var_temp_map[(node.name, node.scope)]        




    def visit_literal_node(self, node: LiteralNode):
        return SSAConst(node.type, node.value)


    def visit_convert_node(self, node: ConvertNode):
        arg = node.expr.accept(self)
        temp = SSATemp(node.type)
        self.add_instr(SSAInstr(SSAOperator.CONVERT, arg, SSAOperand.EMPTY, temp))        
        return temp


    def visit_binary_node(self, node: BinaryNode):
        EMPTY = SSAOperand.EMPTY
        
        if node.token.tag == Tag.OR:
            #labels
            lbl_true = SSALabel()
            lbl_false = SSALabel()
            lbl_end = SSALabel()
            temp = SSATemp(Type.BOOL)

            #tests
            arg1 = node.expr1.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg1, EMPTY, lbl_true))
            arg2 = node.expr2.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IF, arg2, EMPTY, lbl_true))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_false))
            #true
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, True), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, False), EMPTY, temp))
            #self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_end))
        
        elif node.token.tag == Tag.AND:
            #labels
            lbl_false = SSALabel()
            lbl_true = SSALabel()
            lbl_end = SSALabel()
            temp = SSATemp(Type.BOOL)

            #tests
            arg1 = node.expr1.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IFFALSE, arg1, EMPTY, lbl_false))
            arg2 = node.expr2.accept(self)
            self.add_instr(SSAInstr(SSAOperator.IFFALSE, arg2, EMPTY, lbl_false))
                #self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_true))
            #true
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_true))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, True), EMPTY, temp))
            self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_end))
            #false
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_false))
            self.add_instr(SSAInstr(SSAOperator.MOVE, SSAConst(Type.BOOL, False), EMPTY, temp))
                #self.add_instr(SSAInstr(SSAOperator.GOTO, EMPTY, EMPTY, lbl_end))
            #end
            self.add_instr(SSAInstr(SSAOperator.LABEL, EMPTY, EMPTY, lbl_end))            
        else:
            arg1 = node.expr1.accept(self)
            arg2 = node.expr2.accept(self)
            temp = SSATemp(node.type)              
            self.add_instr(SSAInstr(SSA_IC.__OP_MAP[node.operator], arg1, arg2, temp))
        
        return temp




    def visit_unary_node(self, node: UnaryNode):
        arg = node.expr.accept(self)
        temp = SSATemp(node.type)
        
        match node.token.tag:
            case Tag.SUM:
                op = SSAOperator.PLUS
            case Tag.SUB:
                op = SSAOperator.MINUS
            case Tag.NOT:
                op = SSAOperator.NOT
        
        self.add_instr(SSAInstr(op, arg, SSAOperand.EMPTY, temp))
        return temp



    def visit_if_node(self, node: IfNode):
        arg = node.expr.accept(self)
        lbl_out = SSALabel()
        #test
        self.add_instr(SSAInstr(SSAOperator.IFFALSE, arg, SSAOperand.EMPTY, lbl_out))
        #true
        node.stmt.accept(self)
        #out
        self.add_instr(SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_out))


    def visit_else_node(self, node: ElseNode):
        arg = node.expr.accept(self)
        lbl_else = SSALabel()
        lbl_out = SSALabel()
        #test
        self.add_instr(SSAInstr(SSAOperator.IFFALSE, arg, SSAOperand.EMPTY, lbl_else))
        #if-stmt
        node.stmt1.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_out))
        #else-stmt
        self.add_instr(SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_else))
        node.stmt2.accept(self)
        #out
        self.add_instr(SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_out))



    def visit_while_node(self, node: WhileNode):
        lbl_begin = SSALabel()
        lbl_end = SSALabel()
        #test
        self.add_instr(SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_begin))
        arg = node.expr.accept(self)
        self.add_instr(SSAInstr(SSAOperator.IFFALSE, arg, SSAOperand.EMPTY, lbl_end))
        #true
        node.stmt.accept(self)
        self.add_instr(SSAInstr(SSAOperator.GOTO, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_begin))
        #end
        self.add_instr(SSAInstr(SSAOperator.LABEL, SSAOperand.EMPTY, SSAOperand.EMPTY, lbl_end))

    
    def visit_write_node(self, node: WriteNode):
        arg = node.expr.accept(self)
        self.add_instr(SSAInstr(SSAOperator.PRINT, arg, SSAOperand.EMPTY, SSAOperand.EMPTY))


    def visit_read_node(self, node: ReadNode):
        if (node.var.name, node.var.scope) not in self.__var_temp_map:
            temp = SSATemp(node.var.type)
            self.__var_temp_map[(node.var.name, node.var.scope)] = temp
        temp = node.var.accept(self)
        self.add_instr(SSAInstr(SSAOperator.READ, SSAOperand.EMPTY, SSAOperand.EMPTY, temp))


    
        





    OPS = {
        SSAOperator.SUM: lambda a, b: a + b,
        SSAOperator.SUB: lambda a, b: a - b,
        SSAOperator.MUL: lambda a, b: a * b,
        SSAOperator.DIV: lambda a, b: a / b if isinstance(a, float) else a//b,
        SSAOperator.MOD: lambda a, b: a % b,
        SSAOperator.POW: lambda a, b: a ** b,
        SSAOperator.EQ: lambda a, b: a == b,
        SSAOperator.NE: lambda a, b: a != b,
        SSAOperator.LT: lambda a, b: a < b,
        SSAOperator.LE: lambda a, b: a <= b,
        SSAOperator.GT: lambda a, b: a > b,
        SSAOperator.GE: lambda a, b: a >= b,
        SSAOperator.PLUS: lambda a: + a,
        SSAOperator.MINUS: lambda a: - a,
        SSAOperator.NOT: lambda a: not a,
        SSAOperator.CONVERT: lambda a: float(a)
    }

    @staticmethod
    def operate(op: SSAOperator, value1, value2):
        value = SSA_IC.OPS[op](value1, value2)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value

    @staticmethod
    def operate_unary(op: SSAOperator, value):
        value = SSA_IC.OPS[op](value)
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return c_int32(value).value
        elif isinstance(value, float):
            return c_double(value).value

    def interpret(self):
        vars = {}
                
        def get_value(arg):
            if arg.is_temp:
                return vars[arg]
            if arg.is_const:
                return arg.value

        bb = self.bb_sequence[0]
        while bb:
            next_bb = None
            for instr in bb:
                op = instr.op
                result = instr.result
                value1 = get_value(instr.arg1)
                value2 = get_value(instr.arg2)
                
                match op:
                    case SSAOperator.LABEL:
                        continue
                    case SSAOperator.IF:
                        if value1:                    
                            next_bb = self.__bb_from_label(result)
                            break
                    case SSAOperator.IFFALSE:
                        if not value1:
                            next_bb =  self.__bb_from_label(result)
                            break
                    case SSAOperator.GOTO:
                        next_bb = self.__bb_from_label(result)
                        break
                    case SSAOperator.PRINT:
                        if isinstance(value1, float):
                            print(f'output: {value1:.4f}')
                        else:
                            print(f'output: {int(value1)}')
                    case SSAOperator.READ:
                        try:
                            i = input('input: ')
                            match result.type:
                                case Type.BOOL:
                                    i = bool(int(i))
                                case Type.INT:
                                    i = int(i)
                                case Type.REAL:
                                    i = float(i)
                            vars[result] = i
                        except ValueError:
                            print('Entrada de dados inválida! Interpretação encerrada.')
                            return
                    case SSAOperator.CONVERT | SSAOperator.PLUS | SSAOperator.MINUS | SSAOperator.NOT:
                        vars[result] = SSA_IC.operate_unary(op, value1)
                    case SSAOperator.MOVE:
                        vars[result] = value1
                    case _:
                        vars[result] = SSA_IC.operate(op, value1, value2)


            #TRANSIÇÃO DE BLOCOS
            if next_bb:
                bb = next_bb
            else:
                if not bb.successors:
                    bb = None # Fim do programa
                elif len(bb.successors) == 1:
                    bb = bb.successors[0]
                else:
                    bb = bb.successors[-1]
