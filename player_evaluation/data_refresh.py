"""Refresh manually-maintained data files from their external sources."""


def refresh_all():
    """Fetch all externally-sourced data files.

    Fetches CloserMonkey rankings and Eno pitcher rankings. Fangraphs data
    (Stuff+, Statcast, auction values) is already fetched automatically during
    the main pipeline run.
    """
    errors = []

    # CloserMonkey rankings
    try:
        from api.closermonkey import fetch_closermonkey_rankings

        fetch_closermonkey_rankings()
    except Exception as e:
        print(f"Warning: CloserMonkey fetch failed: {e}")
        errors.append("CloserMonkey")

    # Eno pitcher rankings
    try:
        from api.eno import fetch_eno_rankings

        fetch_eno_rankings()
    except Exception as e:
        print(f"Warning: Eno rankings fetch failed: {e}")
        errors.append("Eno")

    if errors:
        print(f"\nSome refreshes failed: {', '.join(errors)}. Using existing local files.")
    else:
        print("\nAll data refreshed successfully.")


if __name__ == "__main__":
    refresh_all()
