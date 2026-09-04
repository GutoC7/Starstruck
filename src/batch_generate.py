import json
import os
import time
import concurrent.futures
from core.generator import PuzzleGenerator

def generate_single_puzzle(size: int, task_id: int):
    """Worker function to generate a single puzzle on a separate CPU thread."""
    generator = PuzzleGenerator(size)
    regions, solution = generator.generate()
    return {
        "size": size,
        "regions": regions,
        "solution": solution,
        "completed": False
    }

def generate_batch(count: int = 50, size: int = 9, filename: str = "puzzles.json"):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    puzzles = []
    
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                data = json.load(f)
                puzzles = data.get("puzzles", [])
                print(f"Loaded existing file with {len(puzzles)} puzzles.")
            except json.JSONDecodeError:
                pass

    start_id = len(puzzles) + 1
    
    print(f"\nIgniting CPU cores! Generating {count} puzzles (Size: {size}x{size})...")
    start_time = time.time()
    
    # Use max_workers=None to automatically use all available CPU cores
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Submit all tasks to the pool
        futures = {executor.submit(generate_single_puzzle, size, i): i for i in range(count)}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                puzzle_data = future.result()
                puzzle_data["id"] = start_id
                puzzles.append(puzzle_data)
                
                # Save incrementally in case the user kills the script
                with open(filepath, "w") as f:
                    json.dump({"puzzles": puzzles}, f, indent=4)
                    
                print(f" -> Success! Puzzle {start_id} saved.")
                start_id += 1
            except Exception as exc:
                print(f"A worker generated an exception: {exc}")
                
    elapsed = time.time() - start_time
    print(f"\nDone! Generated {count} puzzles in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    # Fire up 20 puzzles to test the multi-core speed!
    generate_batch(count=20, size=9)