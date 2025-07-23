import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import json
import os
from datetime import datetime

class TAManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("TA Candidate Management System")
        self.root.geometry("1400x800")
        
        # Data storage
        self.candidates = pd.DataFrame()
        self.original_candidates = pd.DataFrame()
        self.dismissed_candidates = pd.DataFrame()
        self.hired_candidates = {
            'Strong Hire': pd.DataFrame(),
            'Hire': pd.DataFrame(),
            'Weak Hire': pd.DataFrame(),
            'Don\'t Hire': pd.DataFrame()
        }
        
        # Grade mapping for sorting
        self.grade_map = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0,
            '': 0.0, 'N/A': 0.0
        }
        
        self.create_widgets()
        self.load_state()
    
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main candidates tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Available Candidates")
        self.create_main_tab()
        
        # Dismissed candidates tab
        self.dismissed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dismissed_frame, text="Dismissed Candidates")
        self.create_dismissed_tab()
        
        # Hired candidates tabs
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', 'Don\'t Hire']:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=decision)
            self.create_hired_tab(frame, decision)
    
    def create_main_tab(self):
        # Control panel
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # File operations
        ttk.Button(control_frame, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save State", command=self.save_state).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load State", command=self.load_state).pack(side=tk.LEFT, padx=5)
        
        # Sorting controls
        sort_frame = ttk.LabelFrame(control_frame, text="Sort by")
        sort_frame.pack(side=tk.LEFT, padx=20)
        
        self.sort_vars = {}
        sort_options = ['CGPA', 'CS 200 Grade', 'Lab Clash', 'Interview Score']
        for i, option in enumerate(sort_options):
            var = tk.BooleanVar()
            self.sort_vars[option] = var
            ttk.Checkbutton(sort_frame, text=option, variable=var).grid(row=0, column=i, padx=5)
        
        ttk.Button(sort_frame, text="Apply Sort", command=self.apply_sort).grid(row=0, column=len(sort_options), padx=10)
        
        # Main treeview
        self.create_treeview(self.main_frame, "main")
        
        # Context menu for main treeview
        self.create_context_menu()
    
    def create_dismissed_tab(self):
        # Control panel
        control_frame = ttk.Frame(self.dismissed_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Restore Selected", command=self.restore_candidate).pack(side=tk.LEFT, padx=5)
        
        # Dismissed treeview
        self.create_treeview(self.dismissed_frame, "dismissed")
    
    def create_hired_tab(self, parent_frame, decision):
        # Hired treeview
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for this decision type
        tree = ttk.Treeview(tree_frame)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Store reference to tree
        # setattr(self, f"{decision.lower().replace(' ', '_').replace('\\'', '')}_tree", tree)
        setattr(self, f"{decision.lower().replace(' ', '_').replace("'", '')}_tree", tree)

        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(xscrollcommand=h_scroll.set)
    
    def create_treeview(self, parent, tree_type):
        # Frame for treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        tree = ttk.Treeview(tree_frame)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Store reference
        setattr(self, f"{tree_type}_tree", tree)
        
        # Scrollbars
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
            try:
                df = pd.read_csv(file_path)
                
                # Expected columns
                expected_cols = [
                    'Timestamp', 'Full name', 'Roll number', 'Current CGPA', 'If you have declared a major, please specify', 'Grade in CS 200', 'Grade in CS 202 (if taken)',
                    'Would you be able to attend the lectures? MW 11 am to 12:15 pm', 'If you expect a clash with the lecture, please specify the day and duration and timing. For example, Wednesday: 30 minutes, 11 am to 11:30 am.',
                    'Would you be able to attend the lab? Fri 2 pm to 4:50 pm', 'If you have a clash with the lab, please specify the duration and timing. For example, 30 minutes 3 pm to 3:30 pm.',
                    'Mention any potential conflict of interest (Close friends, relatives, significant others). Otherwise, write "No"', 'If you have any prior experience TA\'ing, please mention which course. Otherwise, write "No"',
                    'Why do you want to TA this course?'
                ]
                
                # Add missing columns
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ''
                
                # Add management columns
                df['Interview Score'] = ''
                df['Decision'] = ''
                df['Status'] = 'Available'
                
                self.candidates = df[df['Status'] == 'Available'].copy()
                self.original_candidates = df.copy()
                
                self.refresh_treeview()
                messagebox.showinfo("Success", f"Loaded {len(df)} candidates")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
    
    def refresh_treeview(self):
        # Clear all treeviews
        for tree_name in ['main_tree', 'dismissed_tree']:
            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)
        
        # Clear hired treeviews
        for decision in ['Strong Hire', 'Hire', 'Weak Hire', 'Don\'t Hire']:
            # tree_name = f"{decision.lower().replace(' ', '_').replace('\\'', '')}_tree"
            tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"

            if hasattr(self, tree_name):
                tree = getattr(self, tree_name)
                for item in tree.get_children():
                    tree.delete(item)
        
        # Setup columns and populate main tree
        if not self.candidates.empty:
            self.setup_tree_columns(self.main_tree, self.candidates)
            self.populate_tree(self.main_tree, self.candidates)
        
        # Setup and populate dismissed tree
        if not self.dismissed_candidates.empty:
            self.setup_tree_columns(self.dismissed_tree, self.dismissed_candidates)
            self.populate_tree(self.dismissed_tree, self.dismissed_candidates)
        
        # Setup and populate hired trees
        for decision, df in self.hired_candidates.items():
            if not df.empty:
                # tree_name = f"{decision.lower().replace(' ', '_').replace('\\'', '')}_tree"
                tree_name = f"{decision.lower().replace(' ', '_').replace("'", '')}_tree"

                if hasattr(self, tree_name):
                    tree = getattr(self, tree_name)
                    self.setup_tree_columns(tree, df)
                    self.populate_tree(tree, df)
    
    def setup_tree_columns(self, tree, df):
        # Clear existing columns
        tree['columns'] = ()
        
        # Define columns to show
        # display_cols = ['Timestamp', 'Full Name', 'Roll number', 'Current CGPA', 'Grade in CS 200', 'Grade in CS 202 (if taken)',
                    #    'Available to attend lab? (Yes/No)', 'Interview Score']
        display_cols = [
                    'Full name', 'Roll number', 'Current CGPA', 'If you have declared a major, please specify', 'Grade in CS 200', 'Grade in CS 202 (if taken)',
                    'Would you be able to attend the lectures? MW 11 am to 12:15 pm', 'If you expect a clash with the lecture, please specify the day and duration and timing. For example, Wednesday: 30 minutes, 11 am to 11:30 am.',
                    'Would you be able to attend the lab? Fri 2 pm to 4:50 pm', 'If you have a clash with the lab, please specify the duration and timing. For example, 30 minutes 3 pm to 3:30 pm.',
                    'Mention any potential conflict of interest (Close friends, relatives, significant others). Otherwise, write "No"', 'If you have any prior experience TA\'ing, please mention which course. Otherwise, write "No"',
                    'Why do you want to TA this course?'
                ]
        available_cols = [col for col in display_cols if col in df.columns]
        tree['columns'] = available_cols
        tree['show'] = 'headings'
        
        # Configure columns
        for col in available_cols:
            tree.heading(col, text=col)
            if col in ['CGPA', 'Interview Score']:
                tree.column(col, width=80, anchor='center')
            elif col in ['Grade in CS 200', 'Grade in CS 202 (if taken)']:
                tree.column(col, width=100, anchor='center')
            elif col == 'Roll number':
                tree.column(col, width=100, anchor='center')
            else:
                tree.column(col, width=120)
    
    def populate_tree(self, tree, df):
        for idx, row in df.iterrows():
            values = []
            for col in tree['columns']:
                val = row.get(col, '')
                if pd.isna(val):
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
        
        score = simpledialog.askfloat("Interview Score", "Enter interview score (0-10):", 
                                     minvalue=0, maxvalue=10)
        if score is not None:
            self.candidates.loc[self.candidates.index == idx, 'Interview Score'] = score
            self.refresh_treeview()
    
    def make_decision(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        
        # Create decision dialog
        decision_window = tk.Toplevel(self.root)
        decision_window.title("Make Decision")
        decision_window.geometry("300x200")
        decision_window.transient(self.root)
        decision_window.grab_set()
        
        ttk.Label(decision_window, text="Select decision:").pack(pady=10)
        
        decision_var = tk.StringVar()
        decisions = ['Strong Hire', 'Hire', 'Weak Hire', 'Don\'t Hire']
        
        for decision in decisions:
            ttk.Radiobutton(decision_window, text=decision, variable=decision_var, 
                           value=decision).pack(anchor='w', padx=20)
        
        def apply_decision():
            decision = decision_var.get()
            if decision:
                # Move candidate to hired list
                candidate_row = self.candidates[self.candidates.index == idx].copy()
                candidate_row['Decision'] = decision
                candidate_row['Status'] = 'Decided'
                
                self.hired_candidates[decision] = pd.concat([
                    self.hired_candidates[decision], candidate_row
                ], ignore_index=True)
                
                # Remove from main candidates
                self.candidates = self.candidates[self.candidates.index != idx]
                
                self.refresh_treeview()
                decision_window.destroy()
                messagebox.showinfo("Success", f"Candidate marked as '{decision}'")
        
        ttk.Button(decision_window, text="Apply", command=apply_decision).pack(pady=20)
    
    def dismiss_candidate(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        
        # Move to dismissed
        candidate_row = self.candidates[self.candidates.index == idx].copy()
        candidate_row['Status'] = 'Dismissed'
        
        self.dismissed_candidates = pd.concat([
            self.dismissed_candidates, candidate_row
        ], ignore_index=True)
        
        # Remove from main candidates
        self.candidates = self.candidates[self.candidates.index != idx]
        
        self.refresh_treeview()
        messagebox.showinfo("Success", "Candidate dismissed")
    
    def restore_candidate(self):
        idx = self.get_selected_candidate_index(self.dismissed_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        
        # Move back to main candidates
        candidate_row = self.dismissed_candidates.iloc[[idx]].copy()
        candidate_row['Status'] = 'Available'
        
        self.candidates = pd.concat([self.candidates, candidate_row], ignore_index=True)
        
        # Remove from dismissed
        self.dismissed_candidates = self.dismissed_candidates.drop(
            self.dismissed_candidates.index[idx]
        ).reset_index(drop=True)
        
        self.refresh_treeview()
        messagebox.showinfo("Success", "Candidate restored")
    
    def view_details(self):
        idx = self.get_selected_candidate_index(self.main_tree)
        if idx is None:
            messagebox.showwarning("Warning", "Please select a candidate")
            return
        
        candidate = self.candidates[self.candidates.index == idx].iloc[0]
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Details: {candidate['Name']}")
        details_window.geometry("600x400")
        details_window.transient(self.root)
        
        # Create scrollable text widget
        text_frame = ttk.Frame(details_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate details
        details = ""
        for col in candidate.index:
            if col not in ['Status']:
                details += f"{col}: {candidate[col]}\n\n"
        
        text_widget.insert(tk.END, details)
        text_widget.config(state=tk.DISABLED)
    
    def apply_sort(self):
        if self.candidates.empty:
            return
        
        sort_columns = []
        ascending_order = []
        
        # Build sort criteria based on selected checkboxes
        if self.sort_vars['CGPA'].get():
            sort_columns.append('CGPA')
            ascending_order.append(False)  # Higher CGPA first
        
        if self.sort_vars['CS 200 Grade'].get():
            # Convert grades to numeric for sorting
            self.candidates['CS_200_Numeric'] = self.candidates['Grade in CS 200'].map(self.grade_map)
            sort_columns.append('CS_200_Numeric')
            ascending_order.append(False)  # Higher grade first
        
        if self.sort_vars['Lab Clash'].get():
            # Sort by lab availability (No clash first)
            self.candidates['Lab_Available'] = (
                self.candidates['Available to attend lab? (Yes/No)'].str.lower() == 'yes'
            )
            sort_columns.append('Lab_Available')
            ascending_order.append(False)  # Available first
        
        if self.sort_vars['Interview Score'].get():
            # Convert interview scores to numeric
            self.candidates['Interview_Numeric'] = pd.to_numeric(
                self.candidates['Interview Score'], errors='coerce'
            ).fillna(0)
            sort_columns.append('Interview_Numeric')
            ascending_order.append(False)  # Higher score first
        
        if sort_columns:
            self.candidates = self.candidates.sort_values(
                by=sort_columns, ascending=ascending_order
            ).reset_index(drop=True)
            
            # Clean up temporary columns
            temp_cols = ['CS_200_Numeric', 'Lab_Available', 'Interview_Numeric']
            for col in temp_cols:
                if col in self.candidates.columns:
                    self.candidates = self.candidates.drop(columns=[col])
            
            self.refresh_treeview()
            messagebox.showinfo("Success", "Candidates sorted successfully")
    
    def save_state(self):
        try:
            state = {
                'candidates': self.candidates.to_dict('records') if not self.candidates.empty else [],
                'dismissed_candidates': self.dismissed_candidates.to_dict('records') if not self.dismissed_candidates.empty else [],
                'hired_candidates': {}
            }
            
            for decision, df in self.hired_candidates.items():
                state['hired_candidates'][decision] = df.to_dict('records') if not df.empty else []
            
            with open('ta_management_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            
            messagebox.showinfo("Success", "State saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save state: {str(e)}")
    
    def load_state(self):
        try:
            if os.path.exists('ta_management_state.json'):
                with open('ta_management_state.json', 'r') as f:
                    state = json.load(f)
                
                self.candidates = pd.DataFrame(state.get('candidates', []))
                self.dismissed_candidates = pd.DataFrame(state.get('dismissed_candidates', []))
                
                hired_state = state.get('hired_candidates', {})
                for decision in self.hired_candidates.keys():
                    self.hired_candidates[decision] = pd.DataFrame(hired_state.get(decision, []))
                
                self.refresh_treeview()
                messagebox.showinfo("Success", "State loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load state: {str(e)}")

def main():
    root = tk.Tk()
    app = TAManagementSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()