import tkinter as tk
import random
import time
from tkinter import messagebox

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.revealed = False
        self.flagged = False
        self.adjacent = 0

class Minesweeper:
    def __init__(self, master, rows=9, cols=9, mines=10):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.first_click = True
        self.start_time = None
        self.elapsed = 0
        self.timer_running = False

        self.master.title("Minesweeper")

        #Top control frame
        top = tk.Frame(master)
        top.pack(padx=5, pady=5, anchor="n")

        tk.Label(top, text="Rows:").grid(row=0, column=0)
        self.rows_var = tk.IntVar(value=self.rows)
        tk.Spinbox(top, from_=5, to=30, width=4, textvariable=self.rows_var, command=self._update_size).grid(row=0, column=1)

        tk.Label(top, text="Cols:").grid(row=0, column=2)
        self.cols_var = tk.IntVar(value=self.cols)
        tk.Spinbox(top, from_=5, to=30, width=4, textvariable=self.cols_var, command=self._update_size).grid(row=0, column=3)

        tk.Label(top, text="Mines:").grid(row=0, column=4)
        self.mines_var = tk.IntVar(value=self.mines)
        tk.Spinbox(top, from_=1, to=200, width=6, textvariable=self.mines_var, command=self._update_size).grid(row=0, column=5)

        self.mine_label = tk.Label(top, text=f"Mines: {self.mines}")
        self.mine_label.grid(row=0, column=6, padx=10)

        self.time_label = tk.Label(top, text="Time: 0s")
        self.time_label.grid(row=0, column=7, padx=10)

        tk.Button(top, text="Restart", command=self.restart).grid(row=0, column=8, padx=5)

        #Board frame
        self.board_frame = tk.Frame(master)
        self.board_frame.pack(padx=5, pady=5)

        self._create_board()

    def _update_size(self):
        # Called when spinboxes change
        try:
            r = int(self.rows_var.get())
            c = int(self.cols_var.get())
            m = int(self.mines_var.get())
        except Exception:
            return
        self.rows = max(5, min(30, r))
        self.cols = max(5, min(30, c))
        max_mines = self.rows * self.cols - 1
        m = max(1, min(max_mines, m))
        self.mines = m
        self.mine_label.config(text=f"Mines: {self.mines}")
        self.restart()

    def _create_board(self):
        self.cells = [[Cell(r, c) for c in range(self.cols)] for r in range(self.rows)]
        self.buttons = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        for r in range(self.rows):
            for c in range(self.cols):
                b = tk.Button(self.board_frame, width=2, height=1, font=("TkDefaultFont", 12, 'bold'))
                b.bind("<Button-1>", lambda e, rr=r, cc=c: self.on_left_click(rr, cc))
                b.bind("<Button-3>", lambda e, rr=r, cc=c: self.on_right_click(rr, cc))
                b.grid(row=r, column=c)
                self.buttons[r][c] = b

        #resize window to fit
        self.master.update_idletasks()
        w = self.board_frame.winfo_width() + 20
        h = self.board_frame.winfo_height() + 80
        self.master.minsize(w, h)

    def place_mines(self, safe_r, safe_c):
        # place mines but avoid the first clicked cell and its neighbors
        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        #exclude safe zone
        safe = set()
        for rr in range(safe_r - 1, safe_r + 2):
            for cc in range(safe_c - 1, safe_c + 2):
                if 0 <= rr < self.rows and 0 <= cc < self.cols:
                    safe.add((rr, cc))
        choices = [p for p in positions if p not in safe]
        mines_to_place = min(self.mines, len(choices))
        mines = random.sample(choices, mines_to_place)
        for (r, c) in mines:
            self.cells[r][c].is_mine = True

        # compute adjacent counts
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c].is_mine:
                    continue
                count = 0
                for rr in range(r - 1, r + 2):
                    for cc in range(c - 1, c + 2):
                        if 0 <= rr < self.rows and 0 <= cc < self.cols and self.cells[rr][cc].is_mine:
                            count += 1
                self.cells[r][c].adjacent = count

    def on_left_click(self, r, c):
        if not self.timer_running:
            self.start_timer()
        cell = self.cells[r][c]
        if self.first_click:
            self.place_mines(r, c)
            self.first_click = False
        if cell.flagged or cell.revealed:
            return
        if cell.is_mine:
            self.reveal_mine(r, c)
            self.game_over(False)
            return
        self.reveal_cell(r, c)
        if self.check_win():
            self.game_over(True)

    def on_right_click(self, r, c):
        cell = self.cells[r][c]
        if cell.revealed:
            return
        cell.flagged = not cell.flagged
        b = self.buttons[r][c]
        if cell.flagged:
            b.config(text="F", fg="red")
        else:
            b.config(text="")
        self.update_mine_count()

    def reveal_cell(self, r, c):
        cell = self.cells[r][c]
        b = self.buttons[r][c]
        if cell.revealed or cell.flagged:
            return
        cell.revealed = True
        b.config(relief=tk.SUNKEN)
        if cell.adjacent > 0:
            b.config(text=str(cell.adjacent), disabledforeground=self._color_for_number(cell.adjacent))
        else:
            b.config(text="")
        b.config(state=tk.DISABLED)

        if cell.adjacent == 0:
            #flood fill
            for rr in range(r - 1, r + 2):
                for cc in range(c - 1, c + 2):
                    if (0 <= rr < self.rows and 0 <= cc < self.cols):
                            if not self.cells[rr][cc].revealed:
                                self.reveal_cell(rr, cc)    

    def reveal_mine(self, exploded_r, exploded_c):
        #show all mines
        for r in range(self.rows):
            for c in range(self.cols):
                if self.cells[r][c].is_mine:
                    b = self.buttons[r][c]
                    b.config(text="*", disabledforeground="black")
                    b.config(state=tk.DISABLED)
        #mark exploded
        be = self.buttons[exploded_r][exploded_c]
        be.config(text="*", bg="red")

    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                if not cell.is_mine and not cell.revealed:
                    return False
        return True

    def game_over(self, won):
        self.stop_timer()
        if won:
            messagebox.showinfo("Game Over", f"You won! Time: {self.elapsed:.0f} seconds!")
            # reveal flags
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.cells[r][c].is_mine:
                        self.buttons[r][c].config(text="F", fg="red")
        
        else:
            messagebox.showinfo("Game Over", "You hit a mine! Game over.")
        # disable all buttons
        for r in range(self.rows):
            for c in range(self.cols):
                try:
                    self.buttons[r][c].unbind('<Button-1>')
                    self.buttons[r][c].unbind('<Button-3>')
                except Exception:
                    pass
    def update_mine_count(self):
        flags = sum(1 for r in range(self.rows) for c in range(self.cols) if self.cells[r][c].flagged)
        remaining = max(0, self.mines - flags)
        self.mine_label.config(text=f"Mines: {remaining}")

    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        self._tick()

    def _tick(self):
        if not self.timer_running:
            return
            
        self.elapsed = time.time() - self.start_time
        self.time_label.config(text=f"Time: {int(self.elapsed)}s")
        self.master.after(250, self._tick)

    def stop_timer(self):
        self.timer_running = False

    def restart(self):
        # clear board
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.first_click = True
        self.start_time = None
        self.elapsed = 0
        self.timer_running = False
        self.rows = int(self.rows_var.get())
        self.cols = int(self.cols_var.get())
        self.mines = int(self.mines_var.get())
        max_mines = max(1, self.rows * self.cols - 1)
        if self.mines > max_mines:
            self.mines = max_mines
            self.mines_var.set(self.mines)
        self.mine_label.config(text=f"Mines: {self.mines}")
        self.time_label.config(text="Time: 0s")
        self._create_board()

    def _color_for_number(self, n):
        colors = {
            1: "blue",
            2: "green",
            3: "red",
            4: "dark blue",
            5: "dark red",
            6: "cyan",
            7: "black",
            8: "gray"
        }
        return colors.get(n, "black")

if __name__ == "__main__":
    root = tk.Tk()
    app = Minesweeper(root, rows=9, cols=9, mines=10)
    root.mainloop()
    
        