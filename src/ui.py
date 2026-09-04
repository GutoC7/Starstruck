import pygame
import sys
import math
from typing import List, Tuple
from core.engine import StarstruckEngine, CellState
from core.generator import PuzzleGenerator

class GameUI:
    def __init__(self, engine: StarstruckEngine, generator: PuzzleGenerator):
        pygame.init()
        self.engine = engine
        self.generator = generator
        self.size = engine.size
        self.cell_size = 60
        self.margin = 20
        self.width = self.size * self.cell_size + self.margin * 2
        self.height = self.size * self.cell_size + self.margin * 2
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Starstruck Clone")
        
        self.colors = [
            (115, 147, 203), (219, 132, 107), (145, 178, 122), 
            (218, 187, 104), (171, 104, 114), (133, 119, 173),
            (138, 108, 93), (124, 150, 156), (180, 140, 200), (200, 200, 100)
        ]
        self.bg_color = (20, 24, 34)
        self.line_color = (10, 14, 24)
        self.error_color = (255, 50, 50)
        
        self.font_large = pygame.font.SysFont(None, 64)
        self.font_medium = pygame.font.SysFont(None, 36)
        
        # State machine: "PLAYING", "PAUSED", "WON"
        self.state = "PLAYING"

    def draw_star(self, surface, color, x, y, size):
        """Mathematically draws a 5-pointed star to avoid font compatibility issues."""
        points = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            radius = size if i % 2 == 0 else size / 2.5
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)

    def draw_cross(self, surface, color, x, y, size):
        """Draws an 'X' using lines."""
        offset = size * 0.4
        pygame.draw.line(surface, color, (x - offset, y - offset), (x + offset, y + offset), 3)
        pygame.draw.line(surface, color, (x + offset, y - offset), (x - offset, y + offset), 3)

    def draw_grid(self):
        self.screen.fill(self.bg_color)
        conflicts = self.engine.get_conflicts()
        
        for r in range(self.size):
            for c in range(self.size):
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                reg_id = self.engine.regions[r][c]
                color = self.colors[reg_id % len(self.colors)]
                
                if (r, c) in conflicts:
                    color = self.error_color
                    
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, self.line_color, (x, y, self.cell_size, self.cell_size), 1)
                
                state = self.engine.board[r][c]
                center_x, center_y = x + self.cell_size // 2, y + self.cell_size // 2
                
                if state == CellState.STAR:
                    self.draw_star(self.screen, (255, 255, 255), center_x, center_y, self.cell_size * 0.35)
                elif state == CellState.MARK:
                    self.draw_cross(self.screen, (50, 50, 50), center_x, center_y, self.cell_size)

    def draw_borders(self):
        for r in range(self.size):
            for c in range(self.size):
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                reg = self.engine.regions[r][c]
                
                if c < self.size - 1 and self.engine.regions[r][c+1] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), 4)
                if r < self.size - 1 and self.engine.regions[r+1][c] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), 4)
                
        pygame.draw.rect(self.screen, self.line_color, (self.margin, self.margin, self.size * self.cell_size, self.size * self.cell_size), 4)

    def draw_menu_overlay(self, title, options):
        """Draws a semi-transparent dark overlay with text options."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        title_surf = self.font_large.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(title_surf, title_rect)
        
        for i, text in enumerate(options):
            opt_surf = self.font_medium.render(text, True, (200, 200, 200))
            opt_rect = opt_surf.get_rect(center=(self.width // 2, self.height // 2 + i * 40))
            self.screen.blit(opt_surf, opt_rect)

    def export_images(self):
        """Saves current state as solved, temporarily clears board to save initial state, then restores."""
        # 1. Save Solved State
        self.draw_grid()
        self.draw_borders()
        pygame.image.save(self.screen, "puzzle_solved.png")
        
        # 2. Save Initial State
        temp_board = [row[:] for row in self.engine.board] # Backup board
        self.engine.clear()
        self.draw_grid()
        self.draw_borders()
        pygame.image.save(self.screen, "puzzle_initial.png")
        
        # 3. Restore
        self.engine.board = temp_board
        print("Exported 'puzzle_initial.png' and 'puzzle_solved.png' to project folder!")

    def generate_new_puzzle(self):
        print("Generating new puzzle...")
        regions, _ = self.generator.generate()
        self.engine.regions = regions
        self.engine.clear()
        self.state = "PLAYING"

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.state = "PLAYING"
                            
                    # Keyboard shortcuts for menus
                    if self.state == "PAUSED":
                        if event.key == pygame.K_1: # Reset
                            self.engine.clear()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_2: # Generate New
                            self.generate_new_puzzle()
                            
                    elif self.state == "WON":
                        if event.key == pygame.K_1: # Export
                            self.export_images()
                        elif event.key == pygame.K_2: # Play Again (Reset)
                            self.engine.clear()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_3: # Generate New
                            self.generate_new_puzzle()

                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "PLAYING":
                    x, y = pygame.mouse.get_pos()
                    c = (x - self.margin) // self.cell_size
                    r = (y - self.margin) // self.cell_size
                    
                    if 0 <= r < self.size and 0 <= c < self.size:
                        if event.button == 1:
                            self.engine.toggle_star(r, c)
                        elif event.button == 3:
                            self.engine.toggle_mark(r, c)
                            
                        # Check win condition after every move
                        if self.engine.is_solved():
                            self.state = "WON"

            self.draw_grid()
            self.draw_borders()
            
            if self.state == "PAUSED":
                self.draw_menu_overlay("PAUSED", ["[1] Reset Puzzle", "[2] Generate New Puzzle", "[ESC] Resume"])
            elif self.state == "WON":
                self.draw_menu_overlay("PUZZLE SOLVED!", ["[1] Export Images", "[2] Play Again", "[3] Generate New Puzzle"])
                
            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()