import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from models.candidate import CandidateManager
from services.persistence import load_candidates_csv, save_state, load_state
from services.sorting import sort_candidates
from utils.grade_map import GRADE_MAP

class TAManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("TA Candidate Management System")
        self.root.geometry("1400x800")

        self.manager = CandidateManager()
        self.create_widgets()
        self.load_state()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Available Candidates")
        self.create_main_tab()

        self.dismissed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dismissed_frame, text="Dismissed Candidates")
        self.create_dismissed_tab()

        for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=decision)
            self.create_hired_tab(frame, decision)

    def create_main_tab(self):
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(control_frame, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save State", command=self.save_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load State", command=self.load_state).pack(side=tk.LEFT, padx=5)

        sort_frame = ttk.LabelFrame(control_frame, text="Sort by")
        sort_frame.pack(side=tk.LEFT, padx=20)

        self.sort_vars = {}
        sort_options = ['CGPA', 'CS 200 Grade', 'Lab Clash', 'Interview Score']
        for i, option in enumerate(sort_options):
            var = tk.BooleanVar()
            self.sort_vars[option] = var
            ttk.Checkbutton(sort_frame, text=option, variable=var).grid(row=0, column=i, padx=5)

        ttk.Button(sort_frame, text="Apply Sort", command=self.apply_sort).grid(row=0, column=len(sort_options), padx=10)

        self.create_treeview(self.main_frame, "main")
        self.create_context_menu()

    def create_dismissed_tab(self):
        control_frame = ttk.Frame(self.dismissed_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Restore Selected", command=self.restore_candidate).pack(side=tk.LEFT, padx=5)
        self.create_treeview(self.dismissed_frame, "dismissed")

    def create_hired_tab(self, parent_frame, decision):
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree = ttk.Treeview(tree_frame)
        tree.pack(fill=tk.BOTH, expand=True)
        setattr(self, f"{decision.lower().replace(' ', '_').replace("'", '')}_tree", tree)
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=v_scroll.set)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(xscrollcommand=h_scroll.set)

    def create_treeview(self, parent, tree_type):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree = ttk.Treeview(tree_frame)
        tree.pack(fill=tk.BOTH, expand=True)
        setattr(self, f"{tree_type}_tree", tree)
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=v_scroll.set)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(xscrollcommand=h_scroll.set)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Interview Score", command=self.add_interview_score)
        self.context_menu.add_command(label="Make Decision", command=self.make_decision)
        self.context_menu.add_command(label="Dismiss Candidate", command=self.dismiss_candidate)
        self.context_menu.add_command(label="View Details", command=self.view_details)
        self.main_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            self.main_tree.selection_set(self.main_tree.identify_row(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.manager.load_candidates(file_path)
            self.refresh_treeview()
            messagebox.showinfo("Success", f"Loaded candidates from CSV.")

    def refresh_treeview(self):
        # Clear all treeviews
        for tree_name in ['main_tree', 'dismissed_tree']:
            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
            tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"
            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)
        # Setup columns and populate main tree
        if not self.manager.candidates.empty:
            self.setup_tree_columns(self.main_tree, self.manager.candidates)
            self.populate_tree(self.main_tree, self.manager.candidates)
        if not self.manager.dismissed_candidates.empty:
            self.setup_tree_columns(self.dismissed_tree, self.manager.dismissed_candidates)
            self.populate_tree(self.dismissed_tree, self.manager.dismissed_candidates)
        for decision, df in self.manager.hired_candidates.items():
            if not df.empty:
                tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"
                if hasattr(self, tree_name):
                    tree = getattr(self, tree_name)
                    self.setup_tree_columns(tree, df)
                    self.populate_tree(tree, df)

    def setup_tree_columns(self, tree, df):
        tree['columns'] = ()
        display_cols = self.manager.display_columns
        available_cols = [col for col in display_cols if col in df.columns]
        tree['columns'] = available_cols
        tree['show'] = 'headings'
        for col in available_cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)

    def populate_tree(self, tree, df):
        df = df.fillna('')  # Replace NaN with empty string
        for idx, row in df.iterrows():
            values = []
            for col in tree['columns']:
                val = row.get(col, '')
                if hasattr(val, 'isna') and val.isna():
                    val = ''
                values.append(str(val))
            tree.insert('', 'end', values=values, tags=(str(idx),))

    def get_selected_candidate_index(self, tree):
        selection = tree.selection()
        if not selection:
            return None
        item = selection[0]
        tags = tree.item(item, 'tags')
        if tags:
            return int(tags[0])
        return None

    def add_interview_score(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        score = simpledialog.askfloat("Interview Score", "Enter interview score (0-10):", minvalue=0, maxvalue=10)
        if score is not None:
            self.manager.add_interview_score(idx, score)
            self.refresh_treeview()

    def make_decision(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        decision_window = tk.Toplevel(self.root)
        decision_window.title("Make Decision")
        decision_window.geometry("300x200")
        decision_window.transient(self.root)
        decision_window.grab_set()
        ttk.Label(decision_window, text="Select decision:").pack(pady=10)
        decision_var = tk.StringVar()
        decisions = ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]
        for decision in decisions:
            ttk.Radiobutton(decision_window, text=decision, variable=decision_var, value=decision).pack(anchor='w', padx=20)
        def apply_decision():
            decision = decision_var.get()
            if decision:
                self.manager.make_decision(idx, decision)
                self.refresh_treeview()
                decision_window.destroy()
                messagebox.showinfo("Success", f"Candidate marked as '{decision}'")
        ttk.Button(decision_window, text="Apply", command=apply_decision).pack(pady=20)

    def dismiss_candidate(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        self.manager.dismiss_candidate(idx)
        self.refresh_treeview()
        messagebox.showinfo("Success", "Candidate dismissed")

    def restore_candidate(self):
        idx = self.get_selected_candidate_index(self.dismissed_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        self.manager.restore_candidate(idx)
        self.refresh_treeview()
        messagebox.showinfo("Success", "Candidate restored")

    def view_details(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        candidate = self.manager.candidates.iloc[idx]
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Details: {candidate.get('Full name', 'Candidate')}")
        details_window.geometry("600x400")
        details_window.transient(self.root)
        text_frame = ttk.Frame(details_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        details = ""
        for col in candidate.index:
            if col not in ['Status']:
                details += f"{col}: {candidate[col]}\n\n"
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)

    def apply_sort(self):
        if self.manager.candidates.empty:
            return
        sort_columns = []
        ascending_order = []
        if self.sort_vars['CGPA'].get():
            sort_columns.append('Current CGPA')
            ascending_order.append(False)
        if self.sort_vars['CS 200 Grade'].get():
            sort_columns.append('Grade in CS 200')
            ascending_order.append(False)
        if self.sort_vars['Lab Clash'].get():
            sort_columns.append('Would you be able to attend the lab? Fri 2 pm to 4:50 pm')
            ascending_order.append(False)
        if self.sort_vars['Interview Score'].get():
            sort_columns.append('Interview Score')
            ascending_order.append(False)
        self.manager.sort_candidates(sort_columns, ascending_order)
        self.refresh_treeview()
        messagebox.showinfo("Success", "Candidates sorted successfully")

    def save_state(self):
        try:
            save_state(self.manager)
            messagebox.showinfo("Success", "State saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save state: {str(e)}")

    def load_state(self):
        try:
            load_state(self.manager)
            self.refresh_treeview()
            messagebox.showinfo("Success", "State loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load state: {str(e)}")