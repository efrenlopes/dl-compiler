class LinearScanRegisterAllocation:
    
    def __init__(self, live_ranges, registers):
        self.__live_ranges = live_ranges
        self.__map = {}
        self.__free_registers = list(range(len(live_ranges)-1, -1, -1))        
        self.__active_vars = []
        #registers
        self.register_map = {}
        #spills
        self.spill_map = {}
        self.spill_count = 0
    
        for var in self.__live_ranges: #foreach live ranges in order of increasing start point
            self.__expire_old_ranges(var)                        
            self.__map[var] = self.__free_registers.pop() #a register removed from pool of free registers
            self.__add_to_active_sorted_by_increasing_end_point(var) #add var to active sorted by increasing end point
        
        N = len(registers)
        max_spill = -1
        for var, value in self.__map.items():
            if value < N:
                self.register_map[var] = registers[value]
            else:
                spill = value - N
                self.spill_map[var] = (spill+1) * var.type.size #self.spill_map[var] = spill
                max_spill = max(spill, max_spill)
        if max_spill != -1:
            self.spill_count = max_spill + 1

    def __add_to_active_sorted_by_increasing_end_point(self, var):
        k = 0
        while k < len(self.__active_vars) and self.__live_ranges[self.__active_vars[k]].end <= self.__live_ranges[var].end:
            k += 1
        self.__active_vars.insert(k, var)

    def __expire_old_ranges(self, var):
        for active in self.__active_vars[:]: #foreach in order of increasing end point
            if self.__live_ranges[active].end >= self.__live_ranges[var].start:
                break
            self.__active_vars.remove(active) #remove var from active
            self.__free_registers.append(self.__map[active]) #add register[var] to pool of free registers