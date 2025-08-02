import tkinter as tk
import pandas as pd
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
        # Create control bar first
        self.create_control_bar()

        # Then create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Store tab indices
        self.tab_indices = {}

        # Create main tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Available Candidates")
        self.tab_indices['main'] = self.main_frame
        self.create_treeview(self.main_frame, "main")
        self.create_context_menu()

        # Create dismissed tab
        self.dismissed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dismissed_frame, text="Dismissed Candidates")
        self.tab_indices['dismissed'] = self.dismissed_frame
        self.create_treeview(self.dismissed_frame, "dismissed")

        # Create hired tabs
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=decision)
            self.tab_indices[decision] = frame
            self.create_hired_tab(frame, decision)

    def create_control_bar(self):
        # Create main control frame above notebook
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Search box
        search_label = ttk.Label(control_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 2))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind("<KeyRelease>", self.on_search_change)

        # Buttons
        ttk.Button(control_frame, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save State", command=self.save_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load State", command=self.load_state).pack(side=tk.LEFT, padx=5)

        # Sort controls
        sort_frame = ttk.LabelFrame(control_frame, text="Sort by")
        sort_frame.pack(side=tk.LEFT, padx=20)

        self.sort_vars = {}
        sort_options = ['CGPA', 'CS 200 Grade', 'Lab Clash', 'Interview Score']
        for i, option in enumerate(sort_options):
            var = tk.BooleanVar()
            self.sort_vars[option] = var
            ttk.Checkbutton(sort_frame, text=option, variable=var).grid(row=0, column=i, padx=5)

        ttk.Button(sort_frame, text="Apply Sort", command=self.apply_sort).grid(row=0, column=len(sort_options), padx=10)

    def create_dismissed_tab(self):
        control_frame = ttk.Frame(self.dismissed_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text="Restore Selected", command=self.restore_candidate).pack(side=tk.LEFT, padx=5)
        self.create_treeview(self.dismissed_frame, "dismissed")

    def create_hired_tab(self, parent_frame, decision):
        # Use the same create_treeview method for consistency
        tree = self.create_treeview(parent_frame, decision.lower().replace(' ', '_').replace("'", ''))


    def create_treeview(self, parent, tree_type):
        # Create a container frame
        container_frame = ttk.Frame(parent)
        container_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create the tree and scrollbars
        tree = ttk.Treeview(container_frame)
        
        # Create vertical scrollbar
        v_scroll = ttk.Scrollbar(container_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=v_scroll.set)
        
        # Create horizontal scrollbar
        h_scroll = ttk.Scrollbar(container_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=h_scroll.set)
        
        # Grid layout for proper scrollbar behavior
        tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights
        container_frame.grid_rowconfigure(0, weight=1)
        container_frame.grid_columnconfigure(0, weight=1)
        
        setattr(self, f"{tree_type}_tree", tree)
        return tree

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Interview Score...", command=self.add_interview_score)
        self.context_menu.add_command(label="Make Decision...", command=self.make_decision)
        self.context_menu.add_command(label="Dismiss Candidate...", command=self.dismiss_candidate)
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
            self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            self.manager.load_candidates(file_path)
            self.refresh_treeview()
            # messagebox.showinfo("Success", f"Loaded candidates from CSV.")
        finally:
            # Restore default cursor
            self.root.config(cursor="")
            self.root.update_idletasks()
            # self.manager.load_candidates(file_path)
            # self.refresh_treeview()
            # messagebox.showinfo("Success", f"Loaded candidates from CSV.")

    def refresh_treeview(self):
        # Clear all treeviews
        for tree_name in ['main_tree', 'dismissed_tree']:
            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)

        # Function to filter dataframe based on search
        def filter_df(df):
            if hasattr(self, "search_var"):
                search = self.search_var.get().strip().lower()
                if search:
                    name_col = None
                    id_col = None
                    for col in df.columns:
                        if "name" in col.lower():
                            name_col = col
                        if "roll" in col.lower() or "id" in col.lower():
                            id_col = col
                    if name_col or id_col:
                        mask = pd.Series([False] * len(df))
                        if name_col:
                            mask = mask | df[name_col].astype(str).str.lower().str.contains(search)
                        if id_col:
                            mask = mask | df[id_col].astype(str).str.lower().str.contains(search)
                        return df[mask]
            return df

        # Filter and populate main view
        df = filter_df(self.manager.candidates)
        if not df.empty:
            self.setup_tree_columns(self.main_tree, df)
            self.populate_tree(self.main_tree, df)

        # Filter and populate dismissed view
        df = filter_df(self.manager.dismissed_candidates)
        if not df.empty:
            self.setup_tree_columns(self.dismissed_tree, df)
            self.populate_tree(self.dismissed_tree, df)

        # Filter and populate hired views
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
            tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"
            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)
                df = filter_df(self.manager.hired_candidates[decision])
                if not df.empty:
                    self.setup_tree_columns(tree, df)
                    self.populate_tree(tree, df)

        self.update_tab_labels()  # Update tab labels after refreshing treeviews

    def setup_tree_columns(self, tree, df):
        tree['columns'] = ()
        available_cols = list(df.columns)
        # display_cols = self.manager.display_columns
        # available_cols = [col for col in display_cols if col in df.columns]
        tree['columns'] = available_cols
        tree['show'] = 'headings'
        for col in available_cols:
            # tree.heading(col, text=col)
            tree.heading(col, text=col, command=lambda _col=col, _tree=tree: self.on_treeview_column_click(_tree, _col))
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
            details += f"{col}: {candidate[col]}\n\n"
            # if col not in ['Status']:
            #     details += f"{col}: {candidate[col]}\n\n"
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)

    def get_current_tree(self):
        current_tab = self.notebook.select()
        for key, frame in self.tab_indices.items():
            if str(frame) == str(current_tab):
                if key == 'main':
                    return self.main_tree
                elif key == 'dismissed':
                    return self.dismissed_tree
                else:
                    return getattr(self, f"{key.lower().replace(' ', '_').replace("'", '')}_tree")
        return None

    def apply_sort(self):
        current_tree = self.get_current_tree()
        if not current_tree:
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

        # Get the appropriate DataFrame based on current tab
        current_tab = self.notebook.select()
        for key, frame in self.tab_indices.items():
            if str(frame) == str(current_tab):
                if key == 'main':
                    df = self.manager.candidates
                    if not df.empty and sort_columns:
                        self.manager.candidates = df.sort_values(by=sort_columns, ascending=ascending_order)
                elif key == 'dismissed':
                    df = self.manager.dismissed_candidates
                    if not df.empty and sort_columns:
                        self.manager.dismissed_candidates = df.sort_values(by=sort_columns, ascending=ascending_order)
                else:
                    df = self.manager.hired_candidates[key]
                    if not df.empty and sort_columns:
                        self.manager.hired_candidates[key] = df.sort_values(by=sort_columns, ascending=ascending_order)
                break

        self.refresh_treeview()
        messagebox.showinfo("Success", "Items sorted successfully")

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
            # messagebox.showinfo("Success", "State loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load state: {str(e)}")

    def on_treeview_column_click(self, tree, col):
        try:
            # Determine which DataFrame to sort
            if tree == self.main_tree:
                df = self.manager.candidates
                ascending = getattr(self, 'main_tree_sort_ascending', {}).get(col, True)
                try:
                    self.manager.candidates = df.sort_values(by=col, ascending=ascending).reset_index(drop=True)
                except TypeError as e:
                    # Get the problematic values and their corresponding candidate names
                    problematic_rows = df[pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()]
                    if not problematic_rows.empty:
                        names = problematic_rows['Full name'].tolist()[:2]  # Get first two problematic names
                        message = f"Cannot compare values for candidates:\n{' and '.join(names)}\n\nColumn: {col}"
                        messagebox.showerror("Sorting Error", message)
                        return
                    raise e  # Re-raise if we couldn't identify the problematic rows
                
                self.refresh_treeview()
                if not hasattr(self, 'main_tree_sort_ascending'):
                    self.main_tree_sort_ascending = {}
                self.main_tree_sort_ascending[col] = not ascending

            elif tree == self.dismissed_tree:
                df = self.manager.dismissed_candidates
                ascending = getattr(self, 'dismissed_tree_sort_ascending', {}).get(col, True)
                try:
                    self.manager.dismissed_candidates = df.sort_values(by=col, ascending=ascending).reset_index(drop=True)
                except TypeError as e:
                    problematic_rows = df[pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()]
                    if not problematic_rows.empty:
                        names = problematic_rows['Full name'].tolist()[:2]
                        message = f"Cannot compare values for candidates:\n{' and '.join(names)}\n\nColumn: {col}"
                        messagebox.showerror("Sorting Error", message)
                        return
                    raise e

                self.refresh_treeview()
                if not hasattr(self, 'dismissed_tree_sort_ascending'):
                    self.dismissed_tree_sort_ascending = {}
                self.dismissed_tree_sort_ascending[col] = not ascending

            else:
                # For hired trees
                for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
                    tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"
                    if hasattr(self, tree_name) and tree == getattr(self, tree_name):
                        df = self.manager.hired_candidates[decision]
                        attr_name = f"{tree_name}_sort_ascending"
                        ascending = getattr(self, attr_name, {}).get(col, True)
                        try:
                            self.manager.hired_candidates[decision] = df.sort_values(
                                by=col, ascending=ascending).reset_index(drop=True)
                        except TypeError as e:
                            problematic_rows = df[pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()]
                            if not problematic_rows.empty:
                                names = problematic_rows['Full name'].tolist()[:2]
                                message = f"Cannot compare values for candidates:\n{' and '.join(names)}\n\nColumn: {col}"
                                messagebox.showerror("Sorting Error", message)
                                return
                            raise e

                        self.refresh_treeview()
                        if not hasattr(self, attr_name):
                            setattr(self, attr_name, {})
                        getattr(self, attr_name)[col] = not ascending
                        break

        except Exception as e:
            messagebox.showerror("Sorting Error", 
                f"An unexpected error occurred while sorting column '{col}':\n\n{str(e)}")

    def on_search_change(self, event=None):
        self.refresh_treeview()

    def update_tab_labels(self):
        # Available Candidates
        count = len(self.manager.candidates)
        if count > 0:
            self.notebook.tab(self.tab_indices['main'], text=f"Available Candidates ({count})")
        else:
            self.notebook.tab(self.tab_indices['main'], text="Available Candidates")
        # Dismissed Candidates
        count = len(self.manager.dismissed_candidates)
        if count > 0:
            self.notebook.tab(self.tab_indices['dismissed'], text=f"Dismissed Candidates ({count})")
        else:
            self.notebook.tab(self.tab_indices['dismissed'], text="Dismissed Candidates")
        # Hired Candidates
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', "Don't Hire"]:
            count = len(self.manager.hired_candidates[decision])
            if count > 0:
                self.notebook.tab(self.tab_indices[decision], text=f"{decision} ({count})")
            else:
                self.notebook.tab(self.tab_indices[decision], text=f"{decision}")