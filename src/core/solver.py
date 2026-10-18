from typing import List, Tuple, Set

class StarBattleSolver:
    def __init__(self, size: int, regions: List[List[int]]):
        self.size = size
        self.regions = regions

    def _is_valid(self, r: int, c: int, stars: List[Tuple[int, int]], 
                  col_used: List[bool], region_used: List[bool]) -> bool:
        if col_used[c]:
            return False
        
        reg_id = self.regions[r][c]
        if region_used[reg_id]:
            return False
            
        # King's move (Chebyshev distance) check against existing stars
        for sr, sc in stars:
            if abs(sr - r) <= 1 and abs(sc - c) <= 1:
                return False
                
        return True

    def get_solutions(self, max_count: int = 15) -> List[Set[Tuple[int, int]]]:
        col_used = [False] * self.size
        region_used = [False] * self.size
        stars: List[Tuple[int, int]] = []
        found_solutions: List[Set[Tuple[int, int]]] = []

        def backtrack(row: int):
            if len(found_solutions) >= max_count:
                return

            if row == self.size:
                found_solutions.append(set(stars))
                return

            for col in range(self.size):
                if self._is_valid(row, col, stars, col_used, region_used):
                    reg_id = self.regions[row][col]
                    
                    stars.append((row, col))
                    col_used[col] = True
                    region_used[reg_id] = True
                    
                    backtrack(row + 1)
                    
                    stars.pop()
                    col_used[col] = False
                    region_used[reg_id] = False

        backtrack(0)
        return found_solutions

    def count_solutions(self, max_count: int = 2) -> int:
        return len(self.get_solutions(max_count=max_count))