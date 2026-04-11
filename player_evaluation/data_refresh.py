"""Refresh manually-maintained data files from their external sources."""

from concurrent.futures import ThreadPoolExecutor, as_completed


def refresh_all():
    """Fetch all externally-sourced data files.

    Fetches CloserMonkey rankings and Eno pitcher rankings in parallel.
    Fangraphs data (Stuff+, Statcast, auction values) is already fetched
    automatically during the main pipeline run.
    """
    from api.closermonkey import fetch_closermonkey_rankings
    from api.eno import fetch_eno_rankings

    fetchers = {
        "CloserMonkey": fetch_closermonkey_rankings,
        "Eno": fetch_eno_rankings,
    }

    errors = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(fn): name for name, fn in fetchers.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Warning: {name} fetch failed: {e}")
                errors.append(name)

    if errors:
        print(f"\nSome refreshes failed: {', '.join(errors)}. Using existing local files.")
    else:
        print("\nAll data refreshed successfully.")


if __name__ == "__main__":
    refresh_all()
