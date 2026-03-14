from typing import cast

from dlc.inter.basic_block import BasicBlock
from dlc.inter.interpreter import Interpreter
from dlc.inter.operand import Const, Label, Operand
from dlc.inter.operator import Operator
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa import SSA
from dlc.inter.ssa_operand import TempVersion


@staticmethod
def optimize_ssa(ssa: SSA) -> None:
    changed = True

    while changed:
        changed = False
        changed |= copy_propagation(ssa)
        changed |= constant_folding(ssa)
        changed |= branch_folding(ssa)
        changed |= unreachable_code_elimination(ssa)
        changed |= phi_simplification(ssa)
        changed |= dead_code_elimination(ssa)
        changed |= merge_blocks(ssa)


@staticmethod
def copy_propagation(ssa: SSA) -> bool:
    changed = False
    copies = {}

    # 1. Identificar cópias de forma exaustiva
    for bb in ssa.ir.bb_sequence:
        for instr in bb.body_instrs:
            if instr.op == Operator.MOVE:
                target = instr.result
                source = instr.arg1
                # Se a fonte já é uma cópia de outra coisa, vai até a raiz
                while source in copies:
                    source = copies[source]
                if target != source:
                    copies[target] = source

    # 2. Substituir usos
    for bb in ssa.ir.bb_sequence:
        for instr in bb:            
            # Substituição padrão para arg1 e arg2
            if instr.arg1 in copies:
                instr.arg1 = copies[instr.arg1]
                changed = True
            if instr.arg2 in copies:
                instr.arg2 = copies[instr.arg2]
                changed = True
                
    return changed



@staticmethod
def constant_folding(ssa: SSA) -> bool:
    changed = False
    for bb in ssa.ir.bb_sequence:
        for instr in bb:
            op = instr.op
            arg1 = instr.arg1
            arg2 = instr.arg2
            if isinstance(arg1, Const):
                if op in Interpreter.OP_UNARY:
                    value = Interpreter.OP_UNARY[op](arg1.value)
                elif isinstance(arg2, Const):
                    value = Interpreter.OP_BINARY[op](arg1.value, arg2.value)
                else:
                    continue

                assert(isinstance(instr.result, TempVersion))
                instr.arg1 = Const(instr.result.type, value)
                instr.arg2 = Operand.EMPTY
                instr.op = Operator.MOVE
                changed = True
    return changed




@staticmethod
def branch_folding(ssa: SSA) -> bool:
    changed = False
    for bb in ssa.ir.bb_sequence:
        instr = bb.goto_instr
        # Verifica se a condição do IF é constante (goto do último BB sempre é None)
        if instr and instr.op == Operator.IF and isinstance(instr.arg1, Const): 
            # Decide o caminho a ser tomado
            keep_label, dead_label = (instr.arg2, instr.result) if instr.arg1.value \
                                else (instr.result, instr.arg2)
            bb_dead = ssa.ir.bb_from_label(cast(Label, dead_label))
            bb_dead.predecessors.remove(bb)
            bb.successors.remove(bb_dead)
            # Transforma o IF em um GOTO para o bloco correto
            instr.op = Operator.GOTO
            instr.arg1 = Operand.EMPTY
            instr.arg2 = Operand.EMPTY
            instr.result = keep_label
            changed = True
    return changed




@staticmethod
def unreachable_code_elimination(ssa: SSA) -> bool:
    changed = False
    reachable_labels: set[Label] = set()

    # 1. Coletar todos os labels que são alvos de saltos (GOTO ou IF)
    assert ssa.ir.bb_entry.label_instr is not None
    entry_label = cast(Label, ssa.ir.bb_entry.label_instr.result)
    reachable_labels.add(entry_label)

    for bb in ssa.ir.bb_sequence:
        instr = bb.goto_instr
        if instr:
            for arg in (instr.arg2, instr.result):
                if isinstance(arg, Label):
                    reachable_labels.add(arg)

    # 2. Manter apenas os blocos que são o Entry Block (o primeiro) ou que têm um label atingível
    new_bb_sequence: list[BasicBlock] = []
    for bb in ssa.ir.bb_sequence:
        assert(bb.label_instr is not None)
        if bb.label_instr.result in reachable_labels:
            new_bb_sequence.append(bb)
        else:
            for succ in bb.successors:
                succ.predecessors.remove(bb)
            changed = True # Se o label não está na lista, o bloco morre
    ssa.ir.bb_sequence = new_bb_sequence
    return changed




@staticmethod
def phi_simplification(ssa: SSA) -> bool:
    changed = False
    for bb in ssa.ir.bb_sequence:
        for instr in bb.phi_instrs[:]:
            #Remove dos PHIs os BBs que não existem mais
            assert(isinstance(instr, PhiInstr))
            for path_bb in list(instr.paths):
                if path_bb not in ssa.ir.bb_sequence:
                    changed = True
                    del instr.paths[path_bb]
            #PHIs com valor único são transformados em MOVEs
            if len(instr.paths) == 1:
                instr.op = Operator.MOVE
                instr.arg1 = list(instr.paths.values())[0]
                bb.phi_instrs.remove(instr)
                bb.body_instrs.insert(0, instr)
    return changed








@staticmethod
def dead_code_elimination(ssa: SSA) -> bool:
    changed = False
    use_count: dict[TempVersion, int] = {}

    # 1. Contagem rigorosa
    for bb in ssa.ir.bb_sequence:
        for instr in bb:
            # PHIs são usos
            if isinstance(instr, PhiInstr):
                for version in instr.paths.values():
                    assert(isinstance(version, TempVersion))
                    use_count[version] = use_count.get(version, 0) + 1
            else:
                # Contar usos em arg1 e arg2 de QUALQUER instrução, incluindo IFs
                for arg in (instr.arg1, instr.arg2):
                    if isinstance(arg, TempVersion):
                        use_count[arg] = use_count.get(arg, 0) + 1

    # 2. Remoção
    for bb in ssa.ir.bb_sequence:
        for instr in list(bb):
            res = instr.result
            if isinstance(res, TempVersion) and use_count.get(res, 0) == 0:
                changed = True
                if instr.op == Operator.PHI:
                    bb.phi_instrs.remove(instr)
                else:
                    bb.body_instrs.remove(instr)
    return changed




@staticmethod
def merge_blocks(ssa: SSA) -> bool:
    changed = False
    i = 0
    while i < len(ssa.ir.bb_sequence):
        bb = ssa.ir.bb_sequence[i]
        if len(bb.successors) == 1:
            succ = bb.successors[0]
            if len(succ.predecessors) == 1 and succ != bb:
                # Corrigir PHIs nos sucessores do bloco que vai sumir
                for grandson in succ.successors:
                    for instr in grandson.phi_instrs:
                        # Se a PHI esperava algo vindo de 'succ', agora vem de 'bb'
                        if succ in instr.paths:
                            instr.paths[bb] = instr.paths.pop(succ)
                
                # --- Fusão ---
                bb.goto_instr = succ.goto_instr
                bb.phi_instrs.extend(succ.phi_instrs)
                bb.body_instrs.extend(succ.body_instrs)
                
                bb.successors = succ.successors
                for s in bb.successors:
                    s.predecessors = [bb if p == succ else p for p in s.predecessors]
                
                ssa.ir.bb_sequence.remove(succ)
                changed = True
                #continue 
        i += 1
    return changed