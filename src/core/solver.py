from typing import List, Tuple

class StarBattleSolver:
    def __init__(self, size: int, regions: List[List[int]]):
        self.size = size
        self.regions = regions

    def _is_valid(self, r: int, c: int, stars: List[Tuple[int, int]], 
                  col_used: List[bool], region_used: List[bool]) -> bool:
        """Checks if placing a star at (r, c) violates any game constraints."""
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

    def count_solutions(self, max_count: int = 2) -> int:
        """
        Uses Depth-First Search (DFS) backtracking to find valid solutions.
        Halts early if the number of solutions reaches max_count to save CPU cycles.
        """
        col_used = [False] * self.size
        region_used = [False] * self.size
        stars: List[Tuple[int, int]] = []
        solutions = 0

        def backtrack(row: int):
            nonlocal solutions
            
            # Prune the search tree if we already know the puzzle isn't unique
            if solutions >= max_count:
                return

            # Base case: We successfully placed a star in every row
            if row == self.size:
                solutions += 1
                return

            for col in range(self.size):
                if self._is_valid(row, col, stars, col_used, region_used):
                    reg_id = self.regions[row][col]
                    
                    # Choose
                    stars.append((row, col))
                    col_used[col] = True
                    region_used[reg_id] = True
                    
                    # Explore deeper
                    backtrack(row + 1)
                    
                    # Unchoose (Backtrack)
                    stars.pop()
                    col_used[col] = False
                    region_used[reg_id] = False

        backtrack(0)
        return solutions