"""Analysis functions for fantasy baseball player evaluation"""


def get_top_available_players(df, n=50):
    """Get top N available players sorted by best projection"""
    if "best_projection" not in df.columns:
        print("Warning: best_projection column not found. Computing now...")
        from .data_processors import calculate_projection_metrics

        df = calculate_projection_metrics(df)

    top_players = df.nlargest(n, "best_projection")
    return top_players
