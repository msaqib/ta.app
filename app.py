from gui.main_window import TAManagementSystem
import tkinter as tk

def main():
    root = tk.Tk()
    app = TAManagementSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()