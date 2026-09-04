from core.generator import PuzzleGenerator
from core.engine import StarstruckEngine
from ui import GameUI

def main():
    board_size = 8
    print("Generating initial puzzle... this might take a second.")
    
    generator = PuzzleGenerator(board_size)
    regions, solution = generator.generate()
    
    engine = StarstruckEngine(board_size, regions)
    
    # Pass both to the UI
    app = GameUI(engine, generator)
    app.run()

if __name__ == "__main__":
    main()