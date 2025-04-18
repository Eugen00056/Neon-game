import tkinter as tk
from tkinter import messagebox
import random
import math
from itertools import cycle

class NeonNumbersGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Numbers Game")
        self.root.geometry("1000x700")
        self.root.configure(bg='black')
        
        # Game constants
        self.grid_width = 20
        self.grid_height = 12
        self.cell_size = 40
        self.numbers_range = (10, 57)
        self.numbers_per_target = 50
        self.shake_radius = 3
        self.current_numbers = []
        self.selected_numbers = []
        self.dragging = False
        self.selection_start = None
        self.selection_rect = None
        self.shaking_numbers = {}
        self.occupied_positions = set()
        self.moving_numbers = set()
        
        # Health
        self.health = 100
        self.health_label = tk.Label(root, text=f"Health: {self.health}%", font=("Arial", 16), 
                                    fg="#00ffff", bg="black")
        self.health_label.place(x=10, y=10)
        
        # Counters for divisible sums
        self.divisible_targets = {
            3: {"value": 0, "target": 3, "label": None, "progress": None, "percent": None, 
                "count": 0, "total_count": 0, "current_prime": 3},
            5: {"value": 0, "target": 5, "label": None, "progress": None, "percent": None,
                "count": 0, "total_count": 0, "current_prime": 5},
            7: {"value": 0, "target": 7, "label": None, "progress": None, "percent": None,
                "count": 0, "total_count": 0, "current_prime": 7},
            11: {"value": 0, "target": 11, "label": None, "progress": None, "percent": None,
                 "count": 0, "total_count": 0, "current_prime": 11}
        }
        
        # Create number grid
        self.canvas = tk.Canvas(root, width=1000, height=480, bg="black", highlightthickness=0)
        self.canvas.place(x=0, y=50)
        
        # Create drop zones
        self.drop_zones = {}
        zone_y_position = 500
        for i, divisor in enumerate([3, 5, 7, 11]):
            zone = self.canvas.create_rectangle(50 + i*230, zone_y_position, 
                                             200 + i*230, zone_y_position + 50, 
                                             outline="#00ffff", dash=(5, 2), width=2)
            self.drop_zones[divisor] = zone
        
        # Create counters
        self.create_counters()
        
        # Initialize numbers
        self.initialize_numbers()
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        self.canvas.bind("<Motion>", self.handle_hover)
        
        # Start animation loop
        self.animate_shaking()
    
    def create_counters(self):
        for i, divisor in enumerate([3, 5, 7, 11]):
            label = tk.Label(self.root, text=f"Div by {divisor}: 0/{divisor}", 
                           font=("Arial", 14), fg="#00ffff", bg="black")
            label.place(x=50 + i*230, y=580)
            
            progress = tk.Canvas(self.root, width=150, height=20, bg="black", highlightthickness=0)
            progress.place(x=50 + i*230, y=610)
            progress.create_rectangle(0, 0, 0, 20, fill="#00ffff", outline="")
            
            percent = tk.Label(self.root, text="0% (0/50)", font=("Arial", 12), 
                             fg="#00ffff", bg="black")
            percent.place(x=50 + i*230, y=635)
            
            self.divisible_targets[divisor]["label"] = label
            self.divisible_targets[divisor]["progress"] = progress
            self.divisible_targets[divisor]["percent"] = percent
    
    def initialize_numbers(self):
        self.current_numbers = []
        self.occupied_positions = set()
        
        all_positions = [(col, row) for col in range(self.grid_width) for row in range(self.grid_height)]
        random.shuffle(all_positions)
        
        for i in range(min(len(all_positions), self.grid_width * self.grid_height)):
            col, row = all_positions[i]
            num = random.randint(*self.numbers_range)
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2
            
            text_id = self.canvas.create_text(x, y, text=str(num), 
                                           font=("Arial", 12), fill="#00ffff")
            
            self.current_numbers.append({
                "id": text_id,
                "number": num,
                "row": row,
                "col": col,
                "x": x,
                "y": y,
                "selected": False,
                "original_size": 12
            })
            
            self.occupied_positions.add((col, row))
    
    def add_new_numbers(self, count):
        all_positions = [(col, row) for col in range(self.grid_width) 
                        for row in range(self.grid_height) 
                        if (col, row) not in self.occupied_positions]
        
        random.shuffle(all_positions)
        
        for i in range(min(count, len(all_positions))):
            col, row = all_positions[i]
            num = random.randint(*self.numbers_range)
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2
            
            text_id = self.canvas.create_text(x, y, text=str(num), 
                                            font=("Arial", 12), fill="#00ffff")
            
            self.current_numbers.append({
                "id": text_id,
                "number": num,
                "row": row,
                "col": col,
                "x": x,
                "y": y,
                "selected": False,
                "original_size": 12
            })
            
            self.occupied_positions.add((col, row))
    
    def start_selection(self, event):
        self.selection_start = (event.x, event.y)
        self.selected_numbers = []
        self.dragging = True
        
        for num in self.current_numbers:
            if num["selected"]:
                self.canvas.itemconfig(num["id"], font=("Arial", num["original_size"]))
                num["selected"] = False
        
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
    
    def update_selection(self, event):
        if not self.dragging or not self.selection_start:
            return
            
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        x1, y1 = self.selection_start
        x2, y2 = event.x, event.y
        self.selection_rect = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                         outline="#00ffff", dash=(2, 2), width=1)
        
        min_x, max_x = sorted([x1, x2])
        min_y, max_y = sorted([y1, y2])
        
        for num in self.current_numbers:
            if (min_x <= num["x"] <= max_x and min_y <= num["y"] <= max_y):
                if not num["selected"]:
                    num["selected"] = True
                    self.canvas.itemconfig(num["id"], font=("Arial", num["original_size"] + 4))
            else:
                if num["selected"]:
                    num["selected"] = False
                    self.canvas.itemconfig(num["id"], font=("Arial", num["original_size"]))
    
    def end_selection(self, event):
        self.dragging = False
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        
        self.selected_numbers = [num for num in self.current_numbers if num["selected"]]
        
        if not self.selected_numbers:
            return
            
        total = sum(num["number"] for num in self.selected_numbers)
        
        valid_divisors = [divisor for divisor in self.divisible_targets if total % divisor == 0]
        
        if not valid_divisors:
            messagebox.showinfo("No Divisors", "The sum doesn't divide by any target!")
            self.update_health(-10)
            self.reset_numbers()
            return
        
        chosen_divisor = valid_divisors[0]
        self.move_to_divisor(chosen_divisor)
    
    def handle_hover(self, event):
        if self.moving_numbers:
            return
            
        cursor_x, cursor_y = event.x, event.y
        grid_col = min(max(0, int(cursor_x // self.cell_size)), self.grid_width - 1)
        grid_row = min(max(0, int(cursor_y // self.cell_size)), self.grid_height - 1)
        
        current_shaking = set()
        
        for num in self.current_numbers:
            col_diff = abs(num["col"] - grid_col)
            row_diff = abs(num["row"] - grid_row)
            if col_diff <= self.shake_radius and row_diff <= self.shake_radius:
                current_shaking.add(num["id"])
                if num["id"] not in self.shaking_numbers:
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(0.5, 2.0)
                    dx = math.cos(angle) * distance
                    dy = math.sin(angle) * distance
                    self.shaking_numbers[num["id"]] = (dx, dy)
        
        to_remove = set(self.shaking_numbers.keys()) - current_shaking
        for num_id in to_remove:
            del self.shaking_numbers[num_id]
            for num in self.current_numbers:
                if num["id"] == num_id:
                    self.canvas.coords(num_id, num["x"], num["y"])
                    break
    
    def animate_shaking(self):
        if not self.moving_numbers:
            for num_id, (dx, dy) in list(self.shaking_numbers.items()):
                if random.random() < 0.3:
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(0.5, 2.0)
                    dx = math.cos(angle) * distance
                    dy = math.sin(angle) * distance
                    self.shaking_numbers[num_id] = (dx, dy)
                
                coords = self.canvas.coords(num_id)
                if len(coords) >= 2:
                    original_x, original_y = None, None
                    for num in self.current_numbers:
                        if num["id"] == num_id:
                            original_x, original_y = num["x"], num["y"]
                            break
                    
                    if original_x is not None:
                        self.canvas.coords(num_id, original_x + dx, original_y + dy)
        
        self.root.after(50, self.animate_shaking)
    
    def update_health(self, change):
        self.health = max(0, min(100, self.health + change))
        self.health_label.config(text=f"Health: {self.health}%")
        
        if self.health <= 0:
            messagebox.showinfo("Game Over", "Your health reached 0%!")
            self.root.destroy()
    
    def move_to_divisor(self, divisor):
        selected_sum = sum(num["number"] for num in self.selected_numbers)
        
        if selected_sum % divisor != 0:
            messagebox.showinfo("Wrong Choice", f"The sum doesn't divide by {divisor}!")
            self.update_health(-5)
            self.reset_numbers()
            return
        
        zone_coords = self.canvas.coords(self.drop_zones[divisor])
        target_x = (zone_coords[0] + zone_coords[2]) / 2
        target_y = (zone_coords[1] + zone_coords[3]) / 2
        
        for num in self.selected_numbers:
            if num["id"] in self.shaking_numbers:
                del self.shaking_numbers[num["id"]]
            self.moving_numbers.add(num["id"])
        
        steps = 20
        for num in self.selected_numbers:
            dx = (target_x - num["x"]) / steps
            dy = (target_y - num["y"]) / steps
            
            for step in range(steps):
                self.canvas.after(step * 20, 
                                lambda n=num, dx=dx, dy=dy: self.canvas.move(n["id"], dx, dy) 
                                if n["id"] in [x["id"] for x in self.current_numbers] else None)
        
        self.canvas.after(steps * 20, lambda: self.finish_divisor_update(divisor, selected_sum))
    
    def finish_divisor_update(self, divisor, selected_sum):
        target = self.divisible_targets[divisor]
        
        target["value"] += selected_sum
        target["count"] += len(self.selected_numbers)
        target["total_count"] += len(self.selected_numbers)
        
        if target["total_count"] >= self.numbers_per_target:
            old_prime = target["current_prime"]
            
            # Находим максимальный текущий делитель среди всех целей
            max_current_prime = max(t["current_prime"] for t in self.divisible_targets.values())
            
            # Находим следующее простое число больше максимального текущего
            new_prime = self.get_next_prime(max_current_prime)
            target["current_prime"] = new_prime
            
            target["total_count"] = 0
            target["value"] = 0
            target["target"] = target["current_prime"]
            
            self.update_health(15)
            messagebox.showinfo("Target Updated", 
                              f"New target for {divisor}: {new_prime} (was {old_prime})")
        
        if target["value"] >= target["target"]:
            target["value"] = 0
            self.update_health(5)
        
        self.update_counter_ui(divisor)
        
        for num in self.selected_numbers:
            self.moving_numbers.discard(num["id"])
            self.canvas.delete(num["id"])
            self.current_numbers.remove(num)
            self.occupied_positions.remove((num["col"], num["row"]))
        
        self.add_new_numbers(len(self.selected_numbers))
        self.selected_numbers = []
    
    def update_counter_ui(self, divisor):
        target = self.divisible_targets[divisor]
        progress = min(1, target["value"] / target["target"])
        percent = min(100, target["total_count"] / self.numbers_per_target * 100)
        
        target["label"].config(text=f"Div by {target['current_prime']}: {target['value']}/{target['target']}")
        target["progress"].delete("all")
        target["progress"].create_rectangle(0, 0, 150 * progress, 20, fill="#00ffff", outline="")
        target["percent"].config(text=f"{int(percent)}% ({target['total_count']}/{self.numbers_per_target})")
    
    def reset_numbers(self):
        for num in self.current_numbers:
            if num["id"] in self.shaking_numbers:
                del self.shaking_numbers[num["id"]]
            self.canvas.delete(num["id"])
        self.current_numbers = []
        self.occupied_positions = set()
        self.initialize_numbers()
    
    def get_next_prime(self, n):
        def is_prime(num):
            if num < 2:
                return False
            for i in range(2, int(math.sqrt(num)) + 1):
                if num % i == 0:
                    return False
            return True
        
        candidate = n + 1
        while True:
            if is_prime(candidate):
                return candidate
            candidate += 1

if __name__ == "__main__":
    root = tk.Tk()
    game = NeonNumbersGame(root)
    root.mainloop()