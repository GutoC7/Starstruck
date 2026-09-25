import pygame
import sys
import math
import json
import os
from typing import List, Tuple
from core.engine import StarstruckEngine, CellState
from core.generator import PuzzleGenerator
from core.audio import AudioManager

class GameUI:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        
        self.ANIMATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ANIMATE_EVENT, 40)
        
        self.top_bar = 70 
        
        self.width = 600
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
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
        
        self.state = "MAIN_MENU"
        
        self.engine = None
        self.generator = None
        self.size = 0
        self.current_puzzle_id = None 
        
        self.cell_size = 60
        self.offset_x = 20
        self.offset_y = 90
        
        self.start_time = 0
        self.accumulated_time = 0
        
        self.crt_enabled = False
        self.crt_overlay = None
        self.crt_roll_y = 0          
        self.roll_surface = None     
        self._generate_crt_overlay()
        
        self.puzzles_db = []
        self.current_page = 0
        self.puzzles_per_page = 25
        self.load_puzzles()
        
        # Audio Manager instantiated cleanly inside __init__
        self.audio = AudioManager()

    def _generate_crt_overlay(self):
        self.crt_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 3):
            pygame.draw.line(self.crt_overlay, (0, 0, 0, 50), (0, y), (self.width, y))
            
        pygame.draw.rect(self.crt_overlay, (0, 0, 0, 120), (0, 0, self.width, self.height), 12)
        pygame.draw.rect(self.crt_overlay, (0, 0, 0, 80), (12, 12, self.width-24, self.height-24), 12)
        pygame.draw.rect(self.crt_overlay, (0, 0, 0, 40), (24, 24, self.width-48, self.height-48), 12)

        roll_height = max(100, int(self.height * 0.15)) 
        self.roll_surface = pygame.Surface((self.width, roll_height), pygame.SRCALPHA)
        for y in range(roll_height):
            alpha = int(35 * math.sin(math.pi * (y / roll_height)))
            pygame.draw.line(self.roll_surface, (0, 0, 0, alpha), (0, y), (self.width, y))

    def load_puzzles(self):
        filepath = os.path.join(os.path.dirname(__file__), "puzzles.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                try:
                    data = json.load(f)
                    self.puzzles_db = data.get("puzzles", [])
                except json.JSONDecodeError:
                    self.puzzles_db = []

    def save_progress(self):
        if self.current_puzzle_id:
            for p in self.puzzles_db:
                if p["id"] == self.current_puzzle_id:
                    p["completed"] = True
                    break
            filepath = os.path.join(os.path.dirname(__file__), "puzzles.json")
            with open(filepath, "w") as f:
                json.dump({"puzzles": self.puzzles_db}, f, indent=4)

    def _update_layout(self):
        if self.size > 0:
            available_w = self.width - 40
            available_h = self.height - self.top_bar - 40
            self.cell_size = max(10, min(available_w // self.size, available_h // self.size))
            grid_w = self.size * self.cell_size
            grid_h = self.size * self.cell_size
            self.offset_x = (self.width - grid_w) // 2
            self.offset_y = self.top_bar + (self.height - self.top_bar - grid_h) // 2

    def start_game(self, size: int, pregenerated_data=None):
        self.size = size
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self._update_layout()
        
        self.screen.fill(self.bg_color)
        load_text = self.font_large.render("Loading...", True, (255, 255, 255))
        self.screen.blit(load_text, load_text.get_rect(center=(self.width//2, self.height//2)))
        pygame.display.flip()
        
        if pregenerated_data:
            regions = pregenerated_data["regions"]
            solution = pregenerated_data["solution"]
            self.current_puzzle_id = pregenerated_data["id"]
        else:
            self.generator = PuzzleGenerator(size)
            regions, solution = self.generator.generate()
            self.current_puzzle_id = None
            
        self.engine = StarstruckEngine(size, regions, solution)
        self.accumulated_time = 0
        self.start_time = pygame.time.get_ticks()
        self.state = "PLAYING"

    def return_to_menu(self):
        self.state = "MAIN_MENU"
        self.size = 0
        self.current_puzzle_id = None
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

    def get_time_string(self) -> str:
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
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 3 - 50)))
        
        opt1 = self.font_medium.render("[1] Generate Easy (8x8)", True, (200, 200, 200))
        self.screen.blit(opt1, opt1.get_rect(center=(self.width // 2, self.height // 2 - 20)))
        
        opt2 = self.font_medium.render("[2] Generate Hard (9x9)", True, (200, 200, 200))
        self.screen.blit(opt2, opt2.get_rect(center=(self.width // 2, self.height // 2 + 30)))
        
        opt3 = self.font_medium.render("[3] Play Pre-Generated Levels", True, (145, 178, 122))
        self.screen.blit(opt3, opt3.get_rect(center=(self.width // 2, self.height // 2 + 80)))
        
        crt_text = self.font_medium.render(f"[C] CRT Mode: {'ON' if self.crt_enabled else 'OFF'}", True, (150, 150, 150))
        self.screen.blit(crt_text, crt_text.get_rect(center=(self.width // 2, self.height - 40)))

    def draw_level_select(self):
        self.screen.fill(self.bg_color)
        title = self.font_large.render("SELECT LEVEL", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 60)))
        
        if not self.puzzles_db:
            err = self.font_medium.render("No puzzles found in puzzles.json!", True, self.error_color)
            self.screen.blit(err, err.get_rect(center=(self.width // 2, self.height // 2)))
        else:
            cols = 5
            box_size = 60
            padding = 15
            start_x = (self.width - (cols * box_size + (cols - 1) * padding)) // 2
            start_y = 130
            
            start_idx = self.current_page * self.puzzles_per_page
            end_idx = start_idx + self.puzzles_per_page
            page_puzzles = self.puzzles_db[start_idx:end_idx]
            
            for i, puzzle in enumerate(page_puzzles):
                row = i // cols
                col = i % cols
                x = start_x + col * (box_size + padding)
                y = start_y + row * (box_size + padding)
                
                color = (145, 178, 122) if puzzle.get("completed") else (115, 147, 203)
                pygame.draw.rect(self.screen, color, (x, y, box_size, box_size))
                pygame.draw.rect(self.screen, self.line_color, (x, y, box_size, box_size), 2)
                
                text = self.font_medium.render(str(puzzle["id"]), True, (255, 255, 255))
                self.screen.blit(text, text.get_rect(center=(x + box_size//2, y + box_size//2)))

            # Pagination Arrows
            arrow_y = start_y + 5 * (box_size + padding) + 20
            
            if self.current_page > 0:
                self.btn_prev = pygame.Rect(self.width // 2 - 100, arrow_y, 60, 40)
                pygame.draw.rect(self.screen, (80, 90, 110), self.btn_prev, border_radius=5)
                prev_text = self.font_medium.render("<", True, (255, 255, 255))
                self.screen.blit(prev_text, prev_text.get_rect(center=self.btn_prev.center))
            else:
                self.btn_prev = None
                
            if end_idx < len(self.puzzles_db):
                self.btn_next = pygame.Rect(self.width // 2 + 40, arrow_y, 60, 40)
                pygame.draw.rect(self.screen, (80, 90, 110), self.btn_next, border_radius=5)
                next_text = self.font_medium.render(">", True, (255, 255, 255))
                self.screen.blit(next_text, next_text.get_rect(center=self.btn_next.center))
            else:
                self.btn_next = None

        back = self.font_medium.render("[ESC] Back to Menu", True, (200, 200, 200))
        self.screen.blit(back, back.get_rect(center=(self.width // 2, self.height - 40)))

    def draw_grid(self):
        self.screen.fill(self.bg_color)
        
        time_surf = self.font_large.render(self.get_time_string(), True, (255, 255, 255))
        self.screen.blit(time_surf, time_surf.get_rect(center=(self.width // 2, self.top_bar // 2 + 10)))
        
        if self.current_puzzle_id:
            lvl_surf = self.font_medium.render(f"Level {self.current_puzzle_id}", True, (150, 150, 150))
            self.screen.blit(lvl_surf, lvl_surf.get_rect(topleft=(20, 20)))
        
        conflicts = self.engine.get_conflicts()
        
        for r in range(self.size):
            for c in range(self.size):
                x = self.offset_x + c * self.cell_size
                y = self.offset_y + r * self.cell_size
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

        self.undo_btn = pygame.Rect(self.offset_x, 20, 80, 35)
        pygame.draw.rect(self.screen, (80, 90, 110), self.undo_btn, border_radius=5)
        undo_text = self.font_medium.render("Undo", True, (255, 255, 255))
        self.screen.blit(undo_text, undo_text.get_rect(center=self.undo_btn.center))
        
        self.hint_btn = pygame.Rect(self.offset_x + (self.size * self.cell_size) - 80, 20, 80, 35)
        pygame.draw.rect(self.screen, (100, 140, 110), self.hint_btn, border_radius=5)
        hint_text = self.font_medium.render("Hint", True, (255, 255, 255))
        self.screen.blit(hint_text, hint_text.get_rect(center=self.hint_btn.center))

    def draw_borders(self):
        for r in range(self.size):
            for c in range(self.size):
                x = self.offset_x + c * self.cell_size
                y = self.offset_y + r * self.cell_size
                reg = self.engine.regions[r][c]
                
                if c < self.size - 1 and self.engine.regions[r][c+1] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), 4)
                if r < self.size - 1 and self.engine.regions[r+1][c] != reg:
                    pygame.draw.line(self.screen, self.line_color, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), 4)
                
        pygame.draw.rect(self.screen, self.line_color, (self.offset_x, self.offset_y, self.size * self.cell_size, self.size * self.cell_size), 4)

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
                    
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self._update_layout()
                    self._generate_crt_overlay()
                
                elif event.type == self.ANIMATE_EVENT: 
                    if self.state == "PLAYING" and self.engine and self.engine.animation_queue:
                        self.engine.process_animation_step()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        self.crt_enabled = not self.crt_enabled
                        
                    if self.state == "PLAYING":
                        mods = pygame.key.get_mods()
                        if event.key == pygame.K_z and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                            self.engine.undo()
                        elif event.key == pygame.K_h:
                            self.engine.get_hint()
                            
                    elif self.state == "LEVEL_SELECT":
                        if event.key == pygame.K_LEFT and self.current_page > 0:
                            self.current_page -= 1
                        elif event.key == pygame.K_RIGHT and (self.current_page + 1) * self.puzzles_per_page < len(self.puzzles_db):
                            self.current_page += 1
                            
                    elif self.state == "MAIN_MENU":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.start_game(8)
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.start_game(9)
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self.load_puzzles()
                            self.current_page = 0
                            self.state = "LEVEL_SELECT"
                            
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == "LEVEL_SELECT":
                            self.return_to_menu()
                        elif self.state == "PLAYING":
                            self.accumulated_time += pygame.time.get_ticks() - self.start_time
                            self.state = "PAUSED"
                        elif self.state == "PAUSED":
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                            
                    elif self.state == "PAUSED":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.engine.clear()
                            self.accumulated_time = 0
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            if self.current_puzzle_id:
                                puzzle = next(p for p in self.puzzles_db if p["id"] == self.current_puzzle_id)
                                self.start_game(puzzle["size"], puzzle)
                            else:
                                self.start_game(self.size)
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            self.return_to_menu()
                            
                    elif self.state == "WON":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.export_images()
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.engine.clear()
                            self.accumulated_time = 0
                            self.start_time = pygame.time.get_ticks()
                            self.state = "PLAYING"
                        elif event.key in (pygame.K_3, pygame.K_KP3):
                            if self.current_puzzle_id:
                                self.state = "LEVEL_SELECT"
                            else:
                                self.start_game(self.size)
                        elif event.key in (pygame.K_4, pygame.K_KP4):
                            self.return_to_menu()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "LEVEL_SELECT" and event.button == 1:
                        # Handle Pagination Arrows
                        if self.btn_prev and self.btn_prev.collidepoint(event.pos):
                            self.current_page -= 1
                        elif self.btn_next and self.btn_next.collidepoint(event.pos):
                            self.current_page += 1
                            
                        # Handle Level Selection
                        x, y = pygame.mouse.get_pos()
                        cols = 5
                        box_size = 60
                        padding = 15
                        start_x = (self.width - (cols * box_size + (cols - 1) * padding)) // 2
                        start_y = 130
                        
                        start_idx = self.current_page * self.puzzles_per_page
                        page_puzzles = self.puzzles_db[start_idx : start_idx + self.puzzles_per_page]
                        
                        for i, puzzle in enumerate(page_puzzles):
                            row = i // cols
                            col = i % cols
                            bx = start_x + col * (box_size + padding)
                            by = start_y + row * (box_size + padding)
                            
                            if bx <= x <= bx + box_size and by <= y <= by + box_size:
                                self.start_game(puzzle["size"], puzzle)
                                break
                    
                    elif self.state == "PLAYING":
                        if event.button == 1 and hasattr(self, 'undo_btn') and self.undo_btn.collidepoint(event.pos):
                            self.engine.undo()
                        elif event.button == 1 and hasattr(self, 'hint_btn') and self.hint_btn.collidepoint(event.pos):
                            self.engine.get_hint()
                        else:
                            x, y = event.pos
                            c = (x - self.offset_x) // self.cell_size
                            r = (y - self.offset_y) // self.cell_size
                            
                            if 0 <= r < self.size and 0 <= c < self.size:
                                if event.button == 1:
                                    self.engine.toggle_star(r, c)
                                    if hasattr(self, 'audio'): self.audio.play_star()
                                elif event.button == 3:
                                    self.engine.toggle_mark(r, c)
                                    if hasattr(self, 'audio'): self.audio.play_mark()
                                                    
                elif event.type == pygame.MOUSEMOTION and self.state == "PLAYING":
                    if pygame.mouse.get_pressed()[2]: 
                        x, y = pygame.mouse.get_pos()
                        c = (x - self.offset_x) // self.cell_size
                        r = (y - self.offset_y) // self.cell_size
                        
                        if 0 <= r < self.size and 0 <= c < self.size:
                            if self.engine.board[r][c] == CellState.EMPTY:
                                self.engine.toggle_mark(r, c)
                                if hasattr(self, 'audio'): self.audio.play_mark()

            if self.state == "PLAYING" and self.engine:
                if not self.engine.animation_queue and self.engine.is_solved():
                    self.accumulated_time += pygame.time.get_ticks() - self.start_time
                    self.save_progress() 
                    self.state = "WON"
                    if hasattr(self, 'audio'): self.audio.play_win()

            if self.state == "MAIN_MENU":
                self.draw_main_menu()
            elif self.state == "LEVEL_SELECT":
                self.draw_level_select()
            else:
                self.draw_grid()
                self.draw_borders()
                
                if self.state == "PAUSED":
                    self.draw_menu_overlay("PAUSED", ["[1] Reset", "[2] New/Restart Level", "[3] Main Menu", "[ESC] Resume"])
                elif self.state == "WON":
                    self.draw_menu_overlay("SOLVED!", ["[1] Export Images", "[2] Play Again", "[3] Next/New Level", "[4] Main Menu"])
                
            if self.crt_enabled:
                screen_copy = self.screen.copy()
                screen_copy.set_alpha(70)
                self.screen.blit(screen_copy, (2, 0))
                self.screen.blit(screen_copy, (-2, 0))
                
                self.screen.blit(self.crt_overlay, (0, 0))
                self.screen.blit(self.roll_surface, (0, self.crt_roll_y))
                self.crt_roll_y += 3
                
                if self.crt_roll_y > self.height + 400:
                    self.crt_roll_y = -self.roll_surface.get_height()

            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()
        sys.exit()