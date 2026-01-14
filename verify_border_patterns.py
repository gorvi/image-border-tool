import tkinter as tk
from canvas_widget import CanvasWidget
import sys

def verify_patterns():
    try:
        root = tk.Tk()
        # Hide window
        root.withdraw()
        
        canvas_widget = CanvasWidget(root, width=800, height=800)
        canvas = canvas_widget.canvas
        
        print("Verifying 'grid' pattern...")
        canvas.delete('all')
        canvas_widget.draw_border_pattern('grid', 20, 800, 800, '#000000')
        grid_items = canvas.find_withtag('border')
        print(f"Grid items count: {len(grid_items)}")
        
        if len(grid_items) == 0:
            print("FAIL: No items drawn for 'grid' pattern.")
            sys.exit(1)
            
        # Check if we have items covering all sides (heuristic: count should be significant)
        # 800px width / ~10px spacing = ~80 lines. 
        # Top/Bottom: ~80 * 2 lines (vertical) + ~2 * 2 lines (horizontal)
        # Left/Right: ~2 * 2 lines (vertical) + ~80 * 2 lines (horizontal)
        # Total should be > 100.
        if len(grid_items) < 50:
            print("WARNING: Grid item count seems low for a full grid.")
            
        print("Verifying 'wave' pattern...")
        canvas.delete('all')
        canvas_widget.draw_border_pattern('wave', 20, 800, 800, '#000000')
        wave_items = canvas.find_withtag('border')
        print(f"Wave items count: {len(wave_items)}")
        
        if len(wave_items) == 0:
            print("FAIL: No items drawn for 'wave' pattern.")
            sys.exit(1)
            
        if len(wave_items) < 4:
            print("FAIL: Expected at least 4 wage lines (top, bottom, left, right).")
            sys.exit(1)
            
        print("SUCCESS: Both patterns are generating drawing items.")
        
        root.destroy()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_patterns()
