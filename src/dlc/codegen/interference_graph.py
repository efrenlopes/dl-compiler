from dlc.codegen.live_analysis import LivenessAnalysis
from dlc.inter.ssa_operand import TempVersion


class InterferenceGraph:
    def __init__(self, liveness: LivenessAnalysis, registers: list[str]) -> None:
        self.__liveness = liveness
        self.__registers = registers
        self.__graph: dict[TempVersion, set[TempVersion]] = {}
        self.reg_alloc: dict[TempVersion, str] = {}
        self.mem_alloc: dict[TempVersion, int] = {}
        self.spill_slots_count = 0
        self.__build_graph()
        self.__color_graph()


    def __add_edge(self, u: TempVersion, v: TempVersion) -> None:
        if u == v:
            return
        self.__graph.setdefault(u, set()).add(v)
        self.__graph.setdefault(v, set()).add(u)


    def __build_graph(self) -> None:
        # Inicializa nós do grafo
        for var in self.__liveness.vars:
            self.__graph.setdefault(var, set())

        # Processa cada bloco
        for bb in self.__liveness.ssa.ir.bb_sequence:

            # Conjunto de variáveis vivas na saída do bloco
            live = set(self.__liveness.live_out[bb])


            # -------------------------------------------------
            # INTERFERÊNCIA DENTRO DO BLOCO (BOTTOM-UP)
            # -------------------------------------------------
            instrs = list(reversed(bb.phi_instrs + bb.body_instrs))
            for instr in instrs:
                # DEF
                res = instr.result
                if isinstance(res, TempVersion) and res in self.__liveness.vars:
                    for v in live:
                        self.__add_edge(res, v)
                    live.discard(res)
                # USE
                for arg in (instr.arg1, instr.arg2):
                    if isinstance(arg, TempVersion) and arg in self.__liveness.vars:
                        live.add(arg)



    def __color_graph(self) -> None:
        stack: list[TempVersion] = []
        colors: dict[TempVersion, str] = {}
        temp_graph: dict[TempVersion, set[TempVersion]] = \
            {node: set(neighbors) for node, neighbors in self.__graph.items()}        
        nodes = sorted(temp_graph.keys(), key=lambda x: str(x))
        
        while nodes:
            # Busca nó com grau < K
            for node in nodes:
                if len(temp_graph[node]) < len(self.__registers):
                    stack.append(node)
                    # Remove do grafo temporário
                    for neighbor in temp_graph[node]:
                        temp_graph[neighbor].discard(node)
                    del temp_graph[node]
                    nodes.remove(node)
                    break
            else:
                # Se não achou, escolhe um nó para "Spill"
                node = nodes.pop()
                stack.append(node)

        # 2. Seleção de Cores
        spilled_nodes: list[TempVersion] = []
        while stack:
            node = stack.pop()
            neighbor_colors = {colors[n] for n in self.__graph[node] if n in colors}
            
            for reg in self.__registers:
                if reg not in neighbor_colors:
                    colors[node] = reg
                    self.reg_alloc[node] = reg
                    break
            else:
                colors[node] = '' # Variável vai para a pilha (RAM)
                spilled_nodes.append(node)
        
        for node in spilled_nodes:
            # Pegamos os slots de memória já ocupados pelos vizinhos
            neighbor_mem_slots = {self.mem_alloc[v] for v in self.__graph[node] 
                                if v in self.mem_alloc}
            slot = 0
            while slot in neighbor_mem_slots:
                slot += 1
            if slot >= self.spill_slots_count:
                self.spill_slots_count = slot+1
            self.mem_alloc[node] = slot    # Dicionário específico de memória

        




    def print_allocation_summary(self) -> None:
        """
        Exibe um resumo da alocação permitindo conferir interferências e cores.
        """
        print(f"\n{'='*80}")
        print(f"{'RESUMO DA ALOCAÇÃO DE REGISTRADORES':^80}")
        print(f"{'='*80}")
        print(f"{'Variável':<12} | {'Reg/Cor':<10} | {'Grau':<6} \
                            | {'Vizinhos de Interferência':<35}")
        print(f"{'-'*80}")

        # Ordena as variáveis para facilitar a leitura (ex: t0_1, t0_2...)
        sorted_nodes = sorted(self.__graph.keys(), key=lambda x: str(x))

        for node in sorted_nodes:
            reg = self.reg_alloc.get(node, "N/A")
            neighbors = self.__graph.get(node, set())
            degree = len(neighbors)
            
            # Cria uma string com os vizinhos e suas respectivas cores para conferência
            neighbor_list: list[str] = []
            for n in sorted(neighbors, key=lambda x: str(x)):
                n_color = self.reg_alloc.get(n, "?")
                neighbor_list.append(f"{n}({n_color})")
            
            neighbors_str = ", ".join(neighbor_list)

            print(f"{str(node):<12} | {reg:<10} | {degree:<6} | {neighbors_str}")

        print(f"{'='*80}\n")