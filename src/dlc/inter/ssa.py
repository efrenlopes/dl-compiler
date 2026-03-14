from dlc.inter.basic_block import BasicBlock
from dlc.inter.ir import IR
from dlc.inter.operand import Temp
from dlc.inter.operator import Operator
from dlc.inter.phi_instr import PhiInstr
from dlc.inter.ssa_operand import TempVersion


class SSA:
    def __init__(self, ir: IR) -> None:
        self.ir = ir
        # Replace ALLOCA/STORE
        self.__mem2reg()
        # Dominators
        self.dom: dict[BasicBlock, set[BasicBlock]]
        self.__compute_dominators()
        # Immediate dominators
        self.idom: dict[BasicBlock, BasicBlock|None]
        self.__compute_idom()
        # Dominator Tree
        self.dom_tree: dict[BasicBlock, list[BasicBlock]]
        self.__build_dom_tree()
        # Dominance Frontier
        self.df: dict[BasicBlock, set[BasicBlock]]
        self.__compute_dominance_frontier()
        # Phi insertion
        self.phi_map: dict[BasicBlock, dict[Temp, PhiInstr]]
        self.__insert_phi()
        # Rename
        self.__rename()
        self.__remove_trivial_phis()


    def __str__(self) -> str:
        return str(self.ir)


    def __mem2reg(self) -> None: 
        for bb in self.ir.bb_sequence:
            for instr in bb.body_instrs[:]:
                if instr.op == Operator.ALLOCA:
                    bb.body_instrs.remove(instr)
                elif instr.op in (Operator.STORE, Operator.LOAD):
                    instr.op = Operator.MOVE


    def __compute_dominators(self) -> None:
        self.dom = {self.ir.bb_entry: {self.ir.bb_entry}}
        for bb in self.ir.bb_sequence[1:]:
            self.dom[bb] = set(self.ir.bb_sequence)

        changed = True
        while changed:
            changed = False
            for bb in self.ir.bb_sequence[1:]:
                new_dom = set(self.ir.bb_sequence)
                for p in bb.predecessors:
                    new_dom &= self.dom[p]
                new_dom.add(bb)

                if new_dom != self.dom[bb]:
                    self.dom[bb] = new_dom
                    changed = True
    

    def __compute_idom(self) -> None:
        self.idom = {self.ir.bb_entry: None}
        for bb in self.ir.bb_sequence[1:]:
            strict_doms = self.dom[bb] - {bb}
            # idom is the strict dominator that is not dominated by any other
            for d in strict_doms:
                if all(d == other or d not in self.dom[other] for other in strict_doms):
                    self.idom[bb] = d
                    break


    def __build_dom_tree(self) -> None:
        self.dom_tree = {bb: [] for bb in self.ir.bb_sequence}
        for bb in self.ir.bb_sequence:
            idom_bb = self.idom[bb]
            if idom_bb is not None:
                self.dom_tree[idom_bb].append(bb)

    
    def __compute_dominance_frontier(self) -> None:
        self.df = {bb: set() for bb in self.ir.bb_sequence}
        for bb in self.ir.bb_sequence:
            if len(bb.predecessors) >= 2:
                for runner in bb.predecessors:
                    while runner is not None and runner != self.idom[bb]:
                        self.df[runner].add(bb)
                        runner = self.idom[runner]


    def __insert_phi(self) -> None:
        defsites: dict[Temp, set[BasicBlock]] = {}
        
        # Mapeia onde cada temporário que é definido
        for bb in self.ir.bb_sequence:
            for instr in bb.body_instrs:
                if isinstance(instr.result, Temp):
                    defsites.setdefault(instr.result, set()).add(bb)

        # Ganha PHI qualquer variável com mais de um ponto de definição (defsite)
        phi_vars = [v for v, sites in defsites.items() if len(sites) > 1]

        # Inserção iterada
        self.phi_map = {bb: {} for bb in self.ir.bb_sequence}
        for v in phi_vars:
            worklist = list(defsites[v])
            while worklist:
                n = worklist.pop()
                for y in self.df[n]:
                    if v not in self.phi_map[y]:
                        self.phi_map[y][v] = PhiInstr()
                        # Se y não era um local de definição, adicione ao worklist
                        if y not in defsites[v]:
                            worklist.append(y)


    def __rename(self) -> None:
        # Inicializa pilhas e contadores para cada variável
        self.stack: dict[Temp, list[TempVersion]] = {}
        self.counter: dict[Temp, int] = {}
        
        for bb in self.ir.bb_sequence:
            # Coletamos todos os temporários possíveis (definições e usos)
            for instr in bb:
                for t in (instr.result, instr.arg1, instr.arg2):
                    if isinstance(t, Temp) and t not in self.stack:
                        self.stack.setdefault(t, [])
                        self.counter.setdefault(t, 0)
            # Fazer testes com esse for <<<<<<<<<<<<<<<<<<<<<<<<<<<
            for temp in self.phi_map.get(bb, {}):
                self.stack.setdefault(temp, [])
                self.counter.setdefault(temp, 0)

        self.__rename_block(self.ir.bb_entry)


    def __rename_block(self, bb: BasicBlock) -> None:
        defined_here: list[Temp] = []

        # PHIs
        for temp, phi_instr in self.phi_map.get(bb, {}).items():
            self.counter[temp] += 1
            new_version = TempVersion(temp, self.counter[temp])
            self.stack[temp].append(new_version)
            defined_here.append(temp)
            phi_instr.result = new_version
            bb.phi_instrs.append(phi_instr)

        # instruções
        for instr in bb:
            # arg1
            if isinstance(instr.arg1, Temp) and self.stack[instr.arg1]:
                instr.arg1 = self.stack[instr.arg1][-1]
            # arg2
            if isinstance(instr.arg2, Temp) and self.stack[instr.arg2]:
                instr.arg2 = self.stack[instr.arg2][-1]
            # result
            if isinstance(instr.result, Temp):
                temp = instr.result
                self.counter[temp] += 1
                new_version = TempVersion(temp, self.counter[temp])
                self.stack[temp].append(new_version)
                defined_here.append(temp)
                instr.result = new_version

        # preencher PHIs dos sucessores
        for succ in bb.successors:
            for temp, phi_instr in self.phi_map.get(succ, {}).items():
                if self.stack[temp]:
                    phi_instr.add_path(bb, self.stack[temp][-1])

        # DFS
        for child in self.dom_tree.get(bb, []):
            self.__rename_block(child)

        # POP
        for temp in reversed(defined_here):
            self.stack[temp].pop()


    def __remove_trivial_phis(self) -> None:
        for bb in self.ir.bb_sequence:
            for phi_instr in bb.phi_instrs[:]:
                assert( isinstance(phi_instr, PhiInstr))
                if len(phi_instr.paths) == 1:
                    bb.phi_instrs.remove(phi_instr)






    # def __rename_block(self, bb: BasicBlock) -> None:
    #     # Renomear PHIs - bb pode não estar no mapa phi se não tiver fronteira
    #     phis_in_this_bb = self.phi_map.get(bb, {})
    #     for temp, phi_instr in phis_in_this_bb.items(): 
    #         # Incrementa contador e empilha nova versão para a PHI
    #         self.counter[temp] += 1
    #         new_version = TempVersion(temp, self.counter[temp])
    #         self.stack[temp].append(new_version)
    #         phi_instr.result = new_version
    #         bb.phi_instrs.append(phi_instr)


    #     # Processar instruções (Versionamento Universal)
    #     for instr in bb:
    #         # arg1
    #         temp = instr.arg1
    #         if isinstance(temp, Temp) and self.stack[temp]:
    #             instr.arg1 = self.stack[temp][-1]
    #         # arg2
    #         temp = instr.arg2
    #         if isinstance(temp, Temp) and self.stack[temp]:
    #             instr.arg2 = self.stack[temp][-1]
    #         # result
    #         temp = instr.result
    #         if isinstance(temp, Temp):
    #             self.counter[temp] += 1
    #             new_version = TempVersion(temp, self.counter[temp])
    #             self.stack[temp].append(new_version)
    #             instr.result = new_version


    #     # Preencher argumentos das PHIs nos sucessores
    #     for succ in bb.successors:
    #         for temp, phi_instr in self.phi_map[succ].items():
    #             if temp in self.stack and self.stack[temp]:
    #                 version = self.stack[temp][-1]
    #                 phi_instr.add_path(bb, version)
                    

    #     # DFS na Árvore de Dominância
    #     for child in self.dom_tree.get(bb, []):
    #         self.__rename_block(child)

    #     # Removemos da pilha apenas o que este bloco definiu
    #     for phi_instr in bb:
    #         if isinstance(phi_instr.result, TempVersion):
    #             origin_var = phi_instr.result.origin
    #             if origin_var in self.stack:
    #                 self.stack[origin_var].pop()
