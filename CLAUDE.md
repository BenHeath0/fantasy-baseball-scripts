# Project Rules

## Player Name Normalization

Anytime we read in a player's name (typically keyed as "Player" or "player_name"), we must pass it through `normalize_player_name()` or `normalize_name_column()` from `player_evaluation/utils.py`. This ensures consistent merging across data sources that may differ in apostrophes, diacritics, suffixes, etc.
