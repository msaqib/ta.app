import json
import pandas as pd
import os

def save_state(manager, file_path='ta_management_state.json'):
    state = {
        'candidates': manager.candidates.to_dict('records') if not manager.candidates.empty else [],
        'dismissed_candidates': manager.dismissed_candidates.to_dict('records') if not manager.dismissed_candidates.empty else [],
        'hired_candidates': {}
    }
    for decision, df in manager.hired_candidates.items():
        state['hired_candidates'][decision] = df.to_dict('records') if not df.empty else []
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)

def load_state(manager, file_path='ta_management_state.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            state = json.load(f)
        manager.candidates = pd.DataFrame(state.get('candidates', []))
        manager.dismissed_candidates = pd.DataFrame(state.get('dismissed_candidates', []))
        hired_state = state.get('hired_candidates', {})
        for decision in manager.hired_candidates.keys():
            manager.hired_candidates[decision] = pd.DataFrame(hired_state.get(decision, []))

def load_candidates_csv(file_path):
    return pd.read_csv(file_path)