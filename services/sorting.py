def sort_candidates(df, sort_columns, ascending_order):
    if not sort_columns:
        return df
    return df.sort_values(by=sort_columns, ascending=ascending_order).reset_index(drop=True)