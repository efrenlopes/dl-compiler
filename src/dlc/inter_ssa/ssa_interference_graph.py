from dlc.inter_ssa.ssa_live_analysis import LivenessAnalysis
from dlc.inter_ssa.ssa_operator import SSAOperator


class SSAInterferenceGraph:
    def __init__(self, liveness: LivenessAnalysis, registers: list[str]):
        self.liveness = liveness
        self.registers = registers
        self.graph = {}  # {var: set(vizinhos)}
        self.reg_alloc = {}
        self.mem_alloc = {}
        self.spill_slots_count = 0
        self.__build_graph()
        self.__color_graph()


    def __add_edge(self, u, v):
        if u == v:
            return
        self.graph.setdefault(u, set()).add(v)
        self.graph.setdefault(v, set()).add(u)


    # def __build_graph(self):
    #     for var in self.liveness.vars:
    #         # Garante que a chave exista no self.graph, mesmo sem vizinhos
    #         if var not in self.graph:
    #             self.graph[var] = set()
        
    #     for bb in self.liveness.ssa.ic.bb_sequence:
    #         # Começamos com as variáveis vivas na saída do bloco
    #         live = set(self.liveness.live_out[bb])
            
    #         # Percorremos as instruções de trás para frente (bottom-up)
    #         for instr in reversed(bb.instructions):
    #             res = instr.result
    #             if res.is_temp_version and res in self.liveness.vars:
    #                 # O resultado interfere com tudo que está vivo agora
    #                 for v in live:
    #                     self.__add_edge(res, v)
                    
    #                 # O resultado "morre" ao subir (definição)
    #                 live.discard(res)
                
    #             # Os operandos "nascem" ao subir (uso)
    #             for op in (instr.arg1, instr.arg2):
    #                 if op.is_temp_version and op in self.liveness.vars:
    #                     live.add(op)


    def __build_graph(self):
        # Inicializa nós do grafo
        for var in self.liveness.vars:
            self.graph.setdefault(var, set())

        # Processa cada bloco
        for bb in self.liveness.ssa.ic.bb_sequence:

            # Conjunto de variáveis vivas na saída do bloco
            live = set(self.liveness.live_out[bb])

            # -------------------------------------------------
            # 1. TRATAMENTO DAS PHI NAS ARESTAS (SSA RULE)
            # -------------------------------------------------
            for succ in bb.successors:
                for instr in succ.instructions:
                    if instr.op != SSAOperator.PHI:
                        break

                    dest = instr.result

                    # operando correspondente a este predecessor
                    operand = instr.get_operand_for_predecessor(bb)

                    if operand and operand.is_temp_version and operand in self.liveness.vars:
                        for v in live:
                            self.__add_edge(operand, v)

            # -------------------------------------------------
            # 2. INTERFERÊNCIA DENTRO DO BLOCO (BOTTOM-UP)
            # -------------------------------------------------
            for instr in reversed(bb.instructions):

                # PHI não é tratada aqui
                #if instr.op == SSAOperator.PHI:
                #    continue

                res = instr.result

                # DEF
                if res and res.is_temp_version and res in self.liveness.vars:
                    for v in live:
                        self.__add_edge(res, v)

                    live.discard(res)

                # USE
                for op in (instr.arg1, instr.arg2):
                    if op and op.is_temp_version and op in self.liveness.vars:
                        live.add(op)

    def get_operand_for_predecessor(self, pred):
        """
        Retorna o operando da PHI correspondente ao predecessor.
        """
        for bb, var in self.phi_args:   # lista de (predecessor, variável)
            if bb == pred:
                return var
        return None


    def __color_graph(self):
        stack = []
        temp_graph = {node: set(neighbors) for node, neighbors in self.graph.items()}
        colors = {}
        
        
        # Lista de nomes de registradores reais (ex: rax, rbx...)
        # 1. Simplificação
        nodes = list(temp_graph.keys())
        while nodes:
            # Busca nó com grau < K
            for node in nodes:
                if len(temp_graph[node]) < len(self.registers):
                    stack.append(node)
                    # Remove do grafo temporário
                    for neighbor in temp_graph[node]:
                        temp_graph[neighbor].discard(node)
                    del temp_graph[node]
                    nodes.remove(node)
                    break
            else:
                # Se não achou, escolhe um nó para "Spill" (simplificado aqui)
                node = nodes.pop()
                stack.append(node)
                # (Remove as arestas dele também...)

        # 2. Seleção de Cores
        spilled_nodes = []
        while stack:
            node = stack.pop()
            neighbor_colors = {colors[v] for v in self.graph[node] if v in colors}
            
            for reg in self.registers:
                if reg not in neighbor_colors:
                    colors[node] = reg
                    self.reg_alloc[node] = reg
                    break
            else:
                colors[node] = -1 # Variável vai para a pilha (RAM)
                spilled_nodes.append(node)
        
        for node in spilled_nodes:
            # Pegamos os slots de memória já ocupados pelos vizinhos
            neighbor_mem_slots = {self.mem_alloc[v] for v in self.graph[node] 
                                if v in self.mem_alloc}
            slot = 0
            while slot in neighbor_mem_slots:
                slot += 1
            if slot >= self.spill_slots_count:
                self.spill_slots_count = slot+1
            self.mem_alloc[node] = slot    # Dicionário específico de memória

        




    # def print_allocation_summary(self):
    #     """
    #     Exibe um resumo da alocação permitindo conferir interferências e cores.
    #     """
    #     print(f"\n{'='*80}")
    #     print(f"{'RESUMO DA ALOCAÇÃO DE REGISTRADORES':^80}")
    #     print(f"{'='*80}")
    #     print(f"{'Variável':<12} | {'Reg/Cor':<10} | {'Grau':<6} | {'Vizinhos de Interferência':<35}")
    #     print(f"{'-'*80}")

    #     # Ordena as variáveis para facilitar a leitura (ex: t0_1, t0_2...)
    #     sorted_nodes = sorted(self.graph.keys(), key=lambda x: str(x))

    #     for node in sorted_nodes:
    #         reg = self.colors.get(node, "N/A")
    #         neighbors = self.graph.get(node, set())
    #         degree = len(neighbors)
            
    #         # Cria uma string com os vizinhos e suas respectivas cores para conferência
    #         neighbor_list = []
    #         for n in sorted(neighbors, key=lambda x: str(x)):
    #             n_color = self.colors.get(n, "?")
    #             neighbor_list.append(f"{n}({n_color})")
            
    #         neighbors_str = ", ".join(neighbor_list)

    #         print(f"{str(node):<12} | {reg:<10} | {degree:<6} | {neighbors_str}")

    #     print(f"{'='*80}\n")