import tkinter as tk
from tkinter import messagebox
import random
import time
import os


class MineSafeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("MineSafe")
        self.root.configure(bg="#111827")
        self.root.resizable(False, False)

        self.difficulty_settings = {
            "Easy": {"rows": 8, "cols": 8, "mines": 10},
            "Medium": {"rows": 10, "cols": 10, "mines": 15},
            "Hard": {"rows": 12, "cols": 12, "mines": 25},
        }

        self.best_time_file = "best_time.txt"
        self.best_times = self.load_best_times()

        self.selected_difficulty = tk.StringVar(value="Medium")

        self.rows = 0
        self.cols = 0
        self.mine_count = 0
        self.board = []
        self.buttons = []
        self.revealed = set()
        self.flagged = set()
        self.first_click = True
        self.game_over = False
        self.start_time = None
        self.timer_running = False

        self.build_ui()
        self.start_new_game()

    def build_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#111827", padx=12, pady=12)
        self.top_frame.pack(fill="x")

        self.title_label = tk.Label(
            self.top_frame,
            text="💣 MineSafe",
            font=("Arial", 18, "bold"),
            bg="#111827",
            fg="#f9fafb"
        )
        self.title_label.grid(row=0, column=0, padx=6)

        self.difficulty_menu = tk.OptionMenu(
            self.top_frame,
            self.selected_difficulty,
            *self.difficulty_settings.keys()
        )
        self.difficulty_menu.config(
            font=("Arial", 10, "bold"),
            bg="#374151",
            fg="white",
            width=8,
            activebackground="#4b5563",
            activeforeground="white"
        )
        self.difficulty_menu["menu"].config(
            bg="#374151",
            fg="white",
            font=("Arial", 10)
        )
        self.difficulty_menu.grid(row=0, column=1, padx=6)

        self.restart_button = tk.Button(
            self.top_frame,
            text="Restart",
            command=self.start_new_game,
            font=("Arial", 10, "bold"),
            bg="#22c55e",
            fg="white",
            relief="flat",
            padx=10
        )
        self.restart_button.grid(row=0, column=2, padx=6)

        self.timer_label = tk.Label(
            self.top_frame,
            text="Time: 0s",
            font=("Arial", 11, "bold"),
            bg="#111827",
            fg="#e5e7eb"
        )
        self.timer_label.grid(row=0, column=3, padx=10)

        self.flags_label = tk.Label(
            self.top_frame,
            text="Flags Left: 0",
            font=("Arial", 11, "bold"),
            bg="#111827",
            fg="#e5e7eb"
        )
        self.flags_label.grid(row=0, column=4, padx=10)

        self.best_time_label = tk.Label(
            self.root,
            text="Best Time: --",
            font=("Arial", 11, "bold"),
            bg="#111827",
            fg="#93c5fd"
        )
        self.best_time_label.pack(pady=(0, 4))

        self.status_label = tk.Label(
            self.root,
            text="Click a tile to start the game",
            font=("Arial", 11),
            bg="#111827",
            fg="#d1d5db"
        )
        self.status_label.pack(pady=(0, 8))

        self.board_frame = tk.Frame(self.root, bg="#111827")
        self.board_frame.pack(padx=10, pady=10)

    def load_best_times(self):
        best_times = {"Easy": None, "Medium": None, "Hard": None}
        if os.path.exists(self.best_time_file):
            with open(self.best_time_file, "r") as file:
                for line in file:
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        mode, value = parts
                        if value.isdigit():
                            best_times[mode] = int(value)
        return best_times

    def save_best_times(self):
        with open(self.best_time_file, "w") as file:
            for mode, value in self.best_times.items():
                if value is not None:
                    file.write(f"{mode}:{value}\n")

    def update_best_time_label(self):
        mode = self.selected_difficulty.get()
        best = self.best_times.get(mode)
        if best is None:
            self.best_time_label.config(text=f"Best Time ({mode}): --")
        else:
            self.best_time_label.config(text=f"Best Time ({mode}): {best}s")

    def start_new_game(self):
        for widget in self.board_frame.winfo_children():
            widget.destroy()

        settings = self.difficulty_settings[self.selected_difficulty.get()]
        self.rows = settings["rows"]
        self.cols = settings["cols"]
        self.mine_count = settings["mines"]

        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.buttons = []
        self.revealed = set()
        self.flagged = set()
        self.first_click = True
        self.game_over = False
        self.start_time = None
        self.timer_running = False

        self.timer_label.config(text="Time: 0s")
        self.flags_label.config(text=f"Flags Left: {self.mine_count}")
        self.status_label.config(text="Click a tile to start the game")
        self.update_best_time_label()

        for r in range(self.rows):
            row_buttons = []
            for c in range(self.cols):
                button = tk.Button(
                    self.board_frame,
                    width=3,
                    height=1,
                    font=("Arial", 12, "bold"),
                    bg="#374151",
                    fg="white",
                    relief="raised",
                    activebackground="#4b5563"
                )
                button.grid(row=r, column=c, padx=2, pady=2)
                button.bind("<Button-1>", lambda e, row=r, col=c: self.on_left_click(row, col))
                button.bind("<Button-3>", lambda e, row=r, col=c: self.on_right_click(row, col))
                row_buttons.append(button)
            self.buttons.append(row_buttons)

    def place_mines(self, safe_row, safe_col):
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        positions.remove((safe_row, safe_col))

        mine_positions = random.sample(positions, self.mine_count)
        for row, col in mine_positions:
            self.board[row][col] = -1

        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] != -1:
                    self.board[row][col] = self.count_adjacent_mines(row, col)

    def count_adjacent_mines(self, row, col):
        count = 0
        for r in range(max(0, row - 1), min(self.rows, row + 2)):
            for c in range(max(0, col - 1), min(self.cols, col + 2)):
                if self.board[r][c] == -1:
                    count += 1
        return count

    def on_left_click(self, row, col):
        if self.game_over or (row, col) in self.flagged or (row, col) in self.revealed:
            return

        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False
            self.start_time = time.time()
            self.timer_running = True
            self.update_timer()
            self.status_label.config(text="Game in progress...")

        if self.board[row][col] == -1:
            self.buttons[row][col].config(text="💣", bg="#ef4444", disabledforeground="black")
            self.show_all_mines()
            self.end_game(False)
            return

        self.reveal_cell(row, col)

        if self.check_win():
            self.end_game(True)

    def on_right_click(self, row, col):
        if self.game_over or (row, col) in self.revealed:
            return

        button = self.buttons[row][col]

        if (row, col) in self.flagged:
            self.flagged.remove((row, col))
            button.config(text="", bg="#374151")
        else:
            if len(self.flagged) < self.mine_count:
                self.flagged.add((row, col))
                button.config(text="🚩", bg="#f59e0b")

        self.flags_label.config(text=f"Flags Left: {self.mine_count - len(self.flagged)}")

    def reveal_cell(self, row, col):
        if (row, col) in self.revealed or (row, col) in self.flagged:
            return

        self.revealed.add((row, col))
        button = self.buttons[row][col]
        value = self.board[row][col]

        button.config(relief="sunken", state="disabled", bg="#d1d5db")

        if value > 0:
            button.config(text=str(value), disabledforeground=self.get_number_color(value))
        elif value == 0:
            button.config(text="")
            for r in range(max(0, row - 1), min(self.rows, row + 2)):
                for c in range(max(0, col - 1), min(self.cols, col + 2)):
                    if (r, c) != (row, col):
                        self.reveal_cell(r, c)

    def get_number_color(self, value):
        colors = {
            1: "#2563eb",
            2: "#16a34a",
            3: "#dc2626",
            4: "#7c3aed",
            5: "#b45309",
            6: "#0891b2",
            7: "#111827",
            8: "#6b7280",
        }
        return colors.get(value, "black")

    def show_all_mines(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == -1:
                    self.buttons[row][col].config(text="💣", bg="#fca5a5", fg="black")

    def check_win(self):
        return len(self.revealed) == (self.rows * self.cols - self.mine_count)

    def end_game(self, won):
        self.game_over = True
        self.timer_running = False
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        mode = self.selected_difficulty.get()

        if won:
            self.status_label.config(text="You won the game 🎉")

            previous_best = self.best_times.get(mode)
            if previous_best is None or elapsed < previous_best:
                self.best_times[mode] = elapsed
                self.save_best_times()
                self.update_best_time_label()
                messagebox.showinfo(
                    "Victory 🎉",
                    f"You won in {elapsed} seconds!\nNew best time for {mode} mode!"
                )
            else:
                messagebox.showinfo(
                    "Victory 🎉",
                    f"You won in {elapsed} seconds!"
                )
        else:
            self.status_label.config(text="You hit a mine 💣")
            messagebox.showerror(
                "Game Over",
                f"You lost after {elapsed} seconds."
            )

    def update_timer(self):
        if self.timer_running and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Time: {elapsed}s")
            self.root.after(1000, self.update_timer)


if __name__ == "__main__":
    root = tk.Tk()
    app = MineSafeGame(root)
    root.mainloop()