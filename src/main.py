from core.generator import PuzzleGenerator
from core.engine import StarstruckEngine
from ui import GameUI

def main():
    board_size = 8
    print("Generating puzzle... this might take a second.")
    
    # 1. Generate the puzzle layout
    generator = PuzzleGenerator(board_size)
    regions, solution = generator.generate()
    
    # 2. Initialize the game engine with the generated regions
    engine = StarstruckEngine(board_size, regions)
    
    # 3. Launch the UI
    app = GameUI(engine)
    app.run()

if __name__ == "__main__":
    main()