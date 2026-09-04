import pygame
import sys
import math
from typing import List, Tuple
from core.engine import StarstruckEngine, CellState
from core.generator import PuzzleGenerator

class GameUI:
    def __init__(self):
        pygame.init()
        self.cell_size = 60
        self.margin = 20
        self.top_bar = 70  # Space at the top for the timer
        
        # Initial Main Menu window size
        self.width = 600
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Starstruck")
        
        self.colors = [
            (115, 147, 203), (219, 132, 107), (145, 178, 122), 
            (218, 187, 104), (171, 104, 114), (133, 119, 173),
            (138, 108, 93), (124, 150, 156), (180, 140, 200), (200, 200, 100)
        ]
        self.bg_color = (20, 24, 34)
        self.line_color = (10, 14, 24)
        self.error_color = (255, 50, 50)
        
        self.font_title = pygame.font.SysFont(None, 80)
        self.font_large = pygame.font.SysFont(None, 64)
        self.font_medium = pygame.font.SysFont(None, 36)
        
        # New State Machine
        self.state = "MAIN_MENU"
        
        self.engine = None
        self.generator = None
        self.size = 0
        
        # Timer variables
        self.start_time = 0
        self.accumulated_time = 0

    def start_game(self, size: int):
        """Initializes a new engine/generator and resizes the window."""
        self.size = size
        self.width = self.size * self.cell_size + self.margin * 2
        self.height = self.size * self.cell_size + self.margin * 2 + self.top_bar
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        # Temporarily draw a loading screen since generation takes a second
        self.screen.fill(self.bg_color)
        load_text = self.font_large.render("Generating...", True, (255, 255, 255))
        self.screen.blit(load_text, load_text.get_rect(center=(self.width//2, self.height//2)))
        pygame.display.flip()
        
        self.generator = PuzzleGenerator(size)
        regions, _ = self.generator.generate()
        self.engine = StarstruckEngine(size, regions)
        
        self.accumulated_time = 0
        self.start_time = pygame.time.get_ticks()
        self.state = "PLAYING"

    def return_to_menu(self):
        """Resets the window back to the main menu dimensions."""
        self.state = "MAIN_MENU"
        self.width = 600
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))

    def get_time_string(self) -> str:
        """Calculates formatted MM:SS time, accounting for pauses."""
        if self.state == "PLAYING":
            total_ms = self.accumulated_time + (pygame.time.get_ticks() - self.start_time)
        else:
            total_ms = self.accumulated_time
            
        seconds = total_ms // 1000
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def draw_star(self, surface, color, x, y, size):
        points = []
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            radius = size if i % 2 == 0 else size / 2.5
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)

    def draw_cross(self, surface, color, x, y, size):
        offset = size * 0.4
        pygame.draw.line(surface, color, (x - offset, y - offset), (x + offset, y + offset), 3)
        pygame.draw.line(surface, color, (x + offset, y - offset), (x - offset, y + offset), 3)

    def draw_main_menu(self):
        self.screen.fill(self.bg_color)
        title = self.font_title.render("STARSTRUCK", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 3)))
        
        opt1 = self.font_medium.render("[1] Play Easy (8x8)", True, (200, 200, 200))
        self.screen.blit(opt1, opt1.get_rect(center=(self.width // 2, self.height // 2)))
        
        opt2 = self.font_medium.render("[2] Play Hard (9x9)", True, (200, 200, 200))
        self.screen.blit(opt2, opt2.get_rect(center=(self.width // 2, self.height // 2 + 50)))

    def draw_grid(self):
        self.screen.fill(self.bg_color)
        
        # Draw Timer
        time_surf = self.font_large.render(self.get_time_string(), True, (255, 255, 255))
        self.screen.blit(time_surf, time_surf.get_rect(center=(self.width // 2, self.top_bar // 2 + 10)))
        
        conflicts = self.engine.get_conflicts()
        
        for r in range(self.size):
            for c in range(self.size):
                x = self.margin + c * self.cell_size
                y = self.top_bar + self.margin + r * self.cell_size
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
                y = self.top_bar + self.margin + r * self.cell_size
                reg = self.engine.regions[r][c]
                
                if c < self.size - 1 and self.engine.regions[r][c+1] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), 4)
                if r < self.size - 1 and self.engine.regions[r+1][c] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), 4)
                
        pygame.draw.rect(self.screen, self.line_color, (self.margin, self.top_bar + self.margin, self.size * self.cell_size, self.size * self.cell_size), 4)

    def draw_menu_overlay(self, title, options):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))
        
        title_surf = self.font_large.render(title, True, (255, 255, 255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 3)))
        
        for i, text in enumerate(options):
            opt_surf = self.font_medium.render(text, True, (200, 200, 200))
            self.screen.blit(opt_surf, opt_surf.get_rect(center=(self.width // 2, self.height // 2 + i * 40)))

    def export_images(self):
        self.draw_grid()
        self.draw_borders()
        pygame.image.save(self.screen, "puzzle_solved.png")
        
        temp_board = [row[:] for row in self.engine.board]
        self.engine.clear()
        self.draw_grid()
        self.draw_borders()
        pygame.image.save(self.screen, "puzzle_initial.png")
        
        self.engine.board = temp_board
        print("Exported 'puzzle_initial.png' and 'puzzle_solved.png'!")

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # --- KEYBOARD CONTROLS ---
                elif event.type == pygame.KEYDOWN:
                    if self.state == "MAIN_MENU":
                        if event.key == pygame.K_1:
                            self.start_game(8)
                        elif event.key == pygame.K_2:
                            self.start_game(9)
                            
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == "PLAYING":
                            self.accumulated_time += pygame.time.get_ticks() - self.start_time
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                            
                    elif self.state == "PAUSED":
                        if event.key == pygame.K_1: # Reset
                            self.engine.clear()
                            self.accumulated_time = 0
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_2: # New Puzzle
                            self.start_game(self.size)
                        elif event.key == pygame.K_3: # Main Menu
                            self.return_to_menu()
                            
                    elif self.state == "WON":
                        if event.key == pygame.K_1: # Export
                            self.export_images()
                        elif event.key == pygame.K_2: # Play Again
                            self.engine.clear()
                            self.accumulated_time = 0
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_3: # New Puzzle
                            self.start_game(self.size)
                        elif event.key == pygame.K_4: # Main Menu
                            self.return_to_menu()

                # --- MOUSE CLICK CONTROLS ---
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "PLAYING":
                    x, y = pygame.mouse.get_pos()
                    c = (x - self.margin) // self.cell_size
                    r = (y - self.margin - self.top_bar) // self.cell_size
                    
                    if 0 <= r < self.size and 0 <= c < self.size:
                        if event.button == 1:
                            self.engine.toggle_star(r, c)
                        elif event.button == 3:
                            self.engine.toggle_mark(r, c)
                            
                        if self.engine.is_solved():
                            self.accumulated_time += pygame.time.get_ticks() - self.start_time
                            self.state = "WON"
                            
                # --- MOUSE DRAG CONTROLS (Right Click to Mark) ---
                elif event.type == pygame.MOUSEMOTION and self.state == "PLAYING":
                    if pygame.mouse.get_pressed()[2]: # Index 2 is the Right Mouse Button
                        x, y = pygame.mouse.get_pos()
                        c = (x - self.margin) // self.cell_size
                        r = (y - self.margin - self.top_bar) // self.cell_size
                        
                        if 0 <= r < self.size and 0 <= c < self.size:
                            # Only apply mark if the cell is completely empty (prevents flickering)
                            if self.engine.board[r][c] == CellState.EMPTY:
                                self.engine.toggle_mark(r, c)

            # --- RENDERING ---
            if self.state == "MAIN_MENU":
                self.draw_main_menu()
            else:
                self.draw_grid()
                self.draw_borders()
                
                if self.state == "PAUSED":
                    self.draw_menu_overlay("PAUSED", ["[1] Reset", "[2] New Puzzle", "[3] Main Menu", "[ESC] Resume"])
                elif self.state == "WON":
                    self.draw_menu_overlay("SOLVED!", ["[1] Export Images", "[2] Play Again", "[3] New Puzzle", "[4] Main Menu"])
                
            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()