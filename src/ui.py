import pygame
import sys
from typing import List, Tuple
from core.engine import StarstruckEngine, CellState

class GameUI:
    def __init__(self, engine: StarstruckEngine):
        pygame.init()
        self.engine = engine
        self.size = engine.size
        self.cell_size = 60
        self.margin = 20
        self.width = self.size * self.cell_size + self.margin * 2
        self.height = self.size * self.cell_size + self.margin * 2
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Starstruck Clone")
        
        # A simple distinct color palette for up to 10 regions
        self.colors = [
            (115, 147, 203), (219, 132, 107), (145, 178, 122), 
            (218, 187, 104), (171, 104, 114), (133, 119, 173),
            (138, 108, 93), (124, 150, 156), (180, 140, 200), (200, 200, 100)
        ]
        self.bg_color = (20, 24, 34)
        self.line_color = (10, 14, 24)
        self.error_color = (255, 50, 50)
        
        self.font = pygame.font.SysFont(None, 48)

    def draw_grid(self):
        self.screen.fill(self.bg_color)
        conflicts = self.engine.get_conflicts()
        
        # Draw cells and region colors
        for r in range(self.size):
            for c in range(self.size):
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                
                reg_id = self.engine.regions[r][c]
                color = self.colors[reg_id % len(self.colors)]
                
                # Highlight conflicts in red
                if (r, c) in conflicts:
                    color = self.error_color
                    
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, self.line_color, (x, y, self.cell_size, self.cell_size), 1)
                
                # Draw Star or Mark
                state = self.engine.board[r][c]
                if state == CellState.STAR:
                    # Simple text star for now
                    text = self.font.render("★", True, (255, 255, 255))
                    text_rect = text.get_rect(center=(x + self.cell_size//2, y + self.cell_size//2))
                    self.screen.blit(text, text_rect)
                elif state == CellState.MARK:
                    text = self.font.render("×", True, (50, 50, 50))
                    text_rect = text.get_rect(center=(x + self.cell_size//2, y + self.cell_size//2))
                    self.screen.blit(text, text_rect)

    def draw_borders(self):
        """Draws thicker borders between different regions."""
        for r in range(self.size):
            for c in range(self.size):
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                reg = self.engine.regions[r][c]
                
                # Right border
                if c < self.size - 1 and self.engine.regions[r][c+1] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), 4)
                # Bottom border
                if r < self.size - 1 and self.engine.regions[r+1][c] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), 4)
                
        # Draw outer perimeter
        pygame.draw.rect(self.screen, self.line_color, (self.margin, self.margin, self.size * self.cell_size, self.size * self.cell_size), 4)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    c = (x - self.margin) // self.cell_size
                    r = (y - self.margin) // self.cell_size
                    
                    if 0 <= r < self.size and 0 <= c < self.size:
                        if event.button == 1:  # Left click for Star
                            self.engine.toggle_star(r, c)
                        elif event.button == 3:  # Right click for Mark
                            self.engine.toggle_mark(r, c)

            self.draw_grid()
            self.draw_borders()
            pygame.display.flip()
            
            if self.engine.is_solved():
                print("Puzzle Solved!")
                # We will add win logic here!
                
            clock.tick(60)
            
        pygame.quit()
        sys.exit()