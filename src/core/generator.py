import random
from collections import deque
from typing import List, Tuple, Optional, Set
from .solver import StarBattleSolver

class PuzzleGenerator:
    def __init__(self, size: int):
        self.size = size
        
        # Scale region constraints based on the total board area
        if size >= 12:
            self.min_region_size = 6
            self.max_region_size = 20
        elif size >= 9:
            self.min_region_size = 4
            self.max_region_size = 13
        else:
            self.min_region_size = 2
            self.max_region_size = 12

    def _is_irreducible(self, stars: List[Tuple[int, int]]) -> bool:
        """
        Rejects star layouts that decompose into isolated k x k corner/interval blocks
        (e.g., the 4x4 and 5x5 sub-grid patterns).
        """
        cols = [c for _, c in sorted(stars)]
        n = self.size
        
        # 1. No contiguous interval of k rows (for k in 2..n-1) can span <= k columns
        for k in range(2, n - 1):
            for start_r in range(n - k + 1):
                sub_cols = cols[start_r : start_r + k]
                if max(sub_cols) - min(sub_cols) <= k - 1:
                    return False

        # 2. Prevent 4-star clusters in any of the four 4x4 corners
        if n >= 9:
            corners = [
                (range(0, 4), range(0, 4)),
                (range(0, 4), range(n - 4, n)),
                (range(n - 4, n), range(0, 4)),
                (range(n - 4, n), range(n - 4, n)),
            ]
            for r_range, c_range in corners:
                count = sum(1 for r, c in stars if r in r_range and c in c_range)
                if count >= 3:  # Max 2 stars allowed inside any 4x4 corner
                    return False

        return True

    def _generate_seed_stars(self) -> List[Tuple[int, int]]:
        """Generates a globally entangled star configuration."""
        while True:
            stars: List[Tuple[int, int]] = []
            col_used = [False] * self.size

            def place_star(row: int) -> bool:
                if row == self.size:
                    return True
                cols = list(range(self.size))
                random.shuffle(cols)
                for col in cols:
                    if col_used[col]:
                        continue
                    if any(abs(r - row) <= 1 and abs(c - col) <= 1 for r, c in stars):
                        continue
                    stars.append((row, col))
                    col_used[col] = True
                    if place_star(row + 1):
                        return True
                    stars.pop()
                    col_used[col] = False
                return False

            if place_star(0):
                if self.size < 9 or self._is_irreducible(stars):
                    return stars

    def _grow_initial_regions(self, stars: List[Tuple[int, int]], hard_mode: bool) -> Optional[List[List[int]]]:
        """Grows size-capped regions so no region becomes a 30-cell continent."""
        regions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        region_sizes = {i: 1 for i in range(self.size)}
        frontier: List[Tuple[int, int, int]] = []

        for reg_id, (r, c) in enumerate(stars):
            regions[r][c] = reg_id
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    frontier.append((nr, nc, reg_id))

        while frontier:
            # Prefer smaller regions gently, but cap at max_region_size
            valid_indices = [
                i for i, (_, _, reg_id) in enumerate(frontier)
                if region_sizes[reg_id] < self.max_region_size
            ]
            if not valid_indices:
                # Fallback if all neighboring regions hit the ceiling
                valid_indices = list(range(len(frontier)))

            if hard_mode and random.random() < 0.65:
                min_s = min(region_sizes[frontier[i][2]] for i in valid_indices)
                smallest = [i for i in valid_indices if region_sizes[frontier[i][2]] <= min_s + 1]
                idx = random.choice(smallest)
            else:
                idx = random.choice(valid_indices)

            r, c, reg_id = frontier.pop(idx)
            if regions[r][c] == -1:
                regions[r][c] = reg_id
                region_sizes[reg_id] += 1
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        frontier.append((nr, nc, reg_id))

        if hard_mode:
            if any(s < self.min_region_size or s > self.max_region_size + 2 for s in region_sizes.values()):
                return None

        return regions

    def _is_region_connected(self, regions: List[List[int]], reg_id: int) -> bool:
        """Verifies via BFS that removing a border cell didn't split reg_id in two."""
        cells = [(r, c) for r in range(self.size) for c in range(self.size) if regions[r][c] == reg_id]
        if not cells:
            return False
        visited = {cells[0]}
        queue = deque([cells[0]])
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in cells and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return len(visited) == len(cells)

    def _carve_unique_solution(self, regions: List[List[int]], stars: List[Tuple[int, int]]) -> Optional[List[List[int]]]:
        """
        Solver-Guided Mutation: Finds competing solutions and shifts region borders
        over 'false star' cells to systematically eliminate ambiguity.
        """
        target_set: Set[Tuple[int, int]] = set(stars)
        solver = StarBattleSolver(self.size, regions)
        solutions = solver.get_solutions(max_count=25)

        if len(solutions) == 1:
            return regions

        region_sizes = {i: 0 for i in range(self.size)}
        for r in range(self.size):
            for c in range(self.size):
                region_sizes[regions[r][c]] += 1

        for _ in range(250):
            if len(solutions) == 1:
                return regions

            # Collect all cells where unwanted solutions place stars
            false_stars: Set[Tuple[int, int]] = set()
            for sol in solutions:
                if sol != target_set:
                    false_stars.update(sol - target_set)

            # Find all valid border mutations: (r, c, old_reg, new_reg, is_false_star)
            candidates = []
            for r in range(self.size):
                for c in range(self.size):
                    if (r, c) in target_set:
                        continue  # Never overwrite a true seed star
                    old_reg = regions[r][c]
                    if region_sizes[old_reg] <= self.min_region_size:
                        continue

                    neighbor_regs = set()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size:
                            if regions[nr][nc] != old_reg:
                                neighbor_regs.add(regions[nr][nc])

                    for new_reg in neighbor_regs:
                        if region_sizes[new_reg] < self.max_region_size:
                            priority = 1 if (r, c) in false_stars else 0
                            candidates.append((priority, r, c, old_reg, new_reg))

            if not candidates:
                return None

            # Prioritize mutating cells that directly host false stars
            candidates.sort(key=lambda x: x[0], reverse=True)
            top_pool = [c for c in candidates if c[0] == candidates[0][0]]
            _, r, c, old_reg, new_reg = random.choice(top_pool)

            # Apply tentative border shift
            regions[r][c] = new_reg
            if not self._is_region_connected(regions, old_reg):
                regions[r][c] = old_reg
                continue

            new_solutions = solver.get_solutions(max_count=25)
            # Keep the mutation if it reduces (or maintains) the solution count
            if 1 <= len(new_solutions) <= len(solutions):
                solutions = new_solutions
                region_sizes[old_reg] -= 1
                region_sizes[new_reg] += 1
                if len(solutions) == 1:
                    return regions
            else:
                regions[r][c] = old_reg

        return None

    def _grow_regions_easy(self, stars: List[Tuple[int, int]]) -> List[List[int]]:
        """Legacy random BFS for high-speed 8x8 generation."""
        regions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        frontier: List[Tuple[int, int, int]] = []
        for region_id, (r, c) in enumerate(stars):
            regions[r][c] = region_id
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    frontier.append((nr, nc, region_id))

        while frontier:
            idx = random.randint(0, len(frontier) - 1)
            r, c, region_id = frontier.pop(idx)
            if regions[r][c] == -1:
                regions[r][c] = region_id
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        frontier.append((nr, nc, region_id))
        return regions

    def generate(self) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
        attempts = 0
        hard_mode = self.size >= 9

        while True:
            attempts += 1
            stars = self._generate_seed_stars()
            
            # THE HYBRID BRANCH
            if not hard_mode:
                # Use fast legacy BFS for 8x8
                regions = self._grow_regions_easy(stars)
                solver = StarBattleSolver(self.size, regions)
                if solver.count_solutions(max_count=2) == 1:
                    print(f"[EASY] Puzzle generated after {attempts} attempt(s).")
                    return regions, stars
            else:
                # Use strict border carving for 9x9 and larger
                regions = self._grow_initial_regions(stars, hard_mode=True)
                if regions is None:
                    continue
                regions = self._carve_unique_solution(regions, stars)
                if regions is not None:
                    print(f"[HARD/EXPERT] Unique puzzle carved in {attempts} seed attempt(s).")
                    return regions, stars