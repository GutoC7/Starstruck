import random
from typing import List, Tuple
# We will create this file next!
from .solver import StarBattleSolver

class PuzzleGenerator:
    def __init__(self, size: int):
        self.size = size

    def _generate_seed_stars(self) -> List[Tuple[int, int]]:
        """Places N stars using DFS backtracking to guarantee a valid hidden solution."""
        stars: List[Tuple[int, int]] = []
        col_used = [False] * self.size
        
        def place_star(row: int) -> bool:
            if row == self.size:
                return True
            
            # Shuffle columns to ensure a different base layout every time
            cols = list(range(self.size))
            random.shuffle(cols)
            
            for col in cols:
                if col_used[col]:
                    continue
                
                # Check King's move against already placed stars
                conflict = False
                for r, c in stars:
                    if abs(r - row) <= 1 and abs(c - col) <= 1:
                        conflict = True
                        break
                        
                if conflict:
                    continue
                
                # Place star and traverse deeper
                stars.append((row, col))
                col_used[col] = True
                
                if place_star(row + 1):
                    return True
                    
                # Backtrack
                stars.pop()
                col_used[col] = False
                
            return False
            
        place_star(0)
        return stars

    def _grow_regions(self, stars: List[Tuple[int, int]]) -> List[List[int]]:
        """Multi-source randomized BFS to create organic, Tetris-like puzzle regions."""
        regions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        frontier: List[Tuple[int, int, int]] = []
        
        # 1. Initialize BFS queue with our star seeds
        for region_id, (r, c) in enumerate(stars):
            regions[r][c] = region_id
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if 0 <= r + dr < self.size and 0 <= c + dc < self.size:
                    frontier.append((r + dr, c + dc, region_id))
                    
        # 2. Randomized frontier expansion
        while frontier:
            # Pop a random cell to make shapes organic rather than perfectly diamond/square
            idx = random.randint(0, len(frontier) - 1)
            r, c, region_id = frontier.pop(idx)
            
            if regions[r][c] == -1:
                regions[r][c] = region_id
                
                # Add valid orthogonal neighbors to the queue
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        frontier.append((nr, nc, region_id))
                        
        return regions

    def generate(self) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
        """Generates layouts until it finds one with exactly 1 unique solution."""
        attempts = 0
        while True:
            attempts += 1
            stars = self._generate_seed_stars()
            regions = self._grow_regions(stars)
            
            solver = StarBattleSolver(self.size, regions)
            
            # Prune early: If we find 2 solutions, it's invalid. If 0 (impossible due to our seed), also invalid.
            # We only want exactly 1.
            if solver.count_solutions(max_count=2) == 1:
                print(f"Puzzle generated successfully after {attempts} attempt(s).")
                return regions, stars