import pandas as pd

class CandidateManager:
    def __init__(self):
        self.candidates = pd.DataFrame()
        self.dismissed_candidates = pd.DataFrame()
        self.hired_candidates = {
            'Strong Hire': pd.DataFrame(),
            'Hire': pd.DataFrame(),
            'Weak Hire': pd.DataFrame(),
            "Don't Hire": pd.DataFrame()
        }
        self.display_columns = [
            'Full name', 'Roll number', 'Current CGPA', 'If you have declared a major, please specify', 'Grade in CS 200', 'Grade in CS 202 (if taken)',
            'Would you be able to attend the lectures? MW 11 am to 12:15 pm', 'If you expect a clash with the lecture, please specify the day and duration and timing. For example, Wednesday: 30 minutes, 11 am to 11:30 am.',
            'Would you be able to attend the lab? Fri 2 pm to 4:50 pm', 'If you have a clash with the lab, please specify the duration and timing. For example, 30 minutes 3 pm to 3:30 pm.',
            'Mention any potential conflict of interest (Close friends, relatives, significant others). Otherwise, write "No"', 'If you have any prior experience TA\'ing, please mention which course. Otherwise, write "No"',
            'Why do you wish to TA this course?', 'Interview Score', 'Decision'
        ]

    def load_candidates(self, file_path):
        df = pd.read_csv(file_path)
        for col in self.display_columns:
            if col not in df.columns:
                df[col] = ''
        df['Interview Score'] = ''
        df['Decision'] = ''
        df['Status'] = 'Available'
        self.candidates = df[df['Status'] == 'Available'].copy()
        self.dismissed_candidates = df[df['Status'] == 'Dismissed'].copy()
        for decision in self.hired_candidates.keys():
            self.hired_candidates[decision] = df[df['Decision'] == decision].copy()

    def add_interview_score(self, idx, score):
        self.candidates.at[idx, 'Interview Score'] = score

    def make_decision(self, idx, decision):
        candidate_row = self.candidates.iloc[[idx]].copy()
        candidate_row['Decision'] = decision
        candidate_row['Status'] = 'Decided'
        self.hired_candidates[decision] = pd.concat([self.hired_candidates[decision], candidate_row], ignore_index=True)
        self.candidates = self.candidates.drop(self.candidates.index[idx]).reset_index(drop=True)

    def dismiss_candidate(self, idx):
        candidate_row = self.candidates.iloc[[idx]].copy()
        candidate_row['Status'] = 'Dismissed'
        self.dismissed_candidates = pd.concat([self.dismissed_candidates, candidate_row], ignore_index=True)
        self.candidates = self.candidates.drop(self.candidates.index[idx]).reset_index(drop=True)

    def restore_candidate(self, idx):
        candidate_row = self.dismissed_candidates.iloc[[idx]].copy()
        candidate_row['Status'] = 'Available'
        self.candidates = pd.concat([self.candidates, candidate_row], ignore_index=True)
        self.dismissed_candidates = self.dismissed_candidates.drop(self.dismissed_candidates.index[idx]).reset_index(drop=True)

    def sort_candidates(self, sort_columns, ascending_order):
        if not sort_columns:
            return
        self.candidates = self.candidates.sort_values(by=sort_columns, ascending=ascending_order).reset_index(drop=True)