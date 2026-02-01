# Fantasy Baseball Player Evaluation Tool

A comprehensive tool for evaluating fantasy baseball players using projection data from Fangraphs and other sources.

## ✨ Features

- **Automated Data Fetching**: Automatically fetches projection data, Stuff+, and Statcast data from Fangraphs APIs
- **Keeper Analysis**: Analyzes your roster to determine optimal keeper decisions
- **Draft Preparation**: Generates comprehensive player rankings with additional stats
- **Multiple League Support**: Supports Bush League, Yahoo, and ESPN formats
- **Caching**: Intelligent caching to avoid unnecessary API calls

## 🏗️ Project Structure

```
player-evaluation/
├── main_refactored.py      # New main script with improved functionality
├── config.py               # Configuration constants and settings
├── utils.py                # Utility functions
├── data_fetchers.py        # Data fetching from APIs and files
├── data_processors.py      # Data cleaning and augmentation
├── analysis.py             # Analysis and evaluation functions
├── input_data/             # Local CSV files (fallback data)
├── output/                 # Generated CSV files
└── README.md              # This file
```

## 🚀 Usage

### Basic Draft Analysis

```bash
# Generate player rankings for Bush League
python main_refactored.py --draft --league bush

# Generate rankings using cached data
python main_refactored.py --draft --use-cache
```

### Keeper Analysis

```bash
# Analyze which players to keep
python main_refactored.py --keepers
```

## 📊 Data Sources

### Automatically Fetched from Fangraphs

- **Player Projections**: Auction values and player rater data from multiple systems
- **Stuff+ Data**: Pitcher performance metrics (current season and last month)
- **Statcast Data**: Advanced batting metrics

### Local CSV Files (Fallback/Manual)

- **NFBC ADP**: Average draft position data
- **CloserMonkey**: Reliever rankings
- **Eno Rankings**: Pitcher-specific rankings
- **Baseball Prospectus**: Expert recommendations
- **Bush League Data**: Available players list

## ⚙️ Configuration

Edit `config.py` to customize:

- Projection systems to use
- League settings (teams, budget, positions)
- Data refresh frequency
- File paths

## 🔧 Key Improvements

### From Original Script

1. **Modular Architecture**: Code split into logical modules for better maintainability
2. **Automated Data Fetching**: Eliminates manual CSV downloads for most data sources
3. **Better Error Handling**: Graceful fallbacks when data sources are unavailable
4. **Caching System**: Avoids unnecessary API calls
5. **Enhanced CLI**: More intuitive command-line interface
6. **Improved Documentation**: Better code comments and this README

### Automated vs Manual Data

| Data Source        | Old Method    | New Method        |
| ------------------ | ------------- | ----------------- |
| Player Projections | ✅ API        | ✅ API (improved) |
| Stuff+ Data        | ❌ Manual CSV | ✅ Automated API  |
| Statcast Data      | ❌ Manual CSV | ✅ Automated API  |
| NFBC ADP           | ❌ Manual CSV | ⚠️ Manual CSV\*   |
| CloserMonkey       | ❌ Manual CSV | ⚠️ Manual CSV\*   |

\*Future enhancement: These could be automated with web scraping

## 🚦 Migration from Original Script

To use the new version:

1. **Keep your existing data**: The new script can still use your `input_data/` CSV files as fallbacks
2. **Use new main script**: Run `python main_refactored.py` instead of `python main.py`
3. **Updated arguments**: New CLI interface with more options
4. **Caching**: Use `--use-cache` flag to use cached data instead of fetching fresh

## 📈 Example Output

### Keeper Analysis

```
Keeper Analysis (Threshold: -5.0)
==================================================

Shohei Ohtani (Cost: $45)
  Current Status: Available
  Recommendation: KEEP
    steamer: $12.3 ✅
    thebatx: $8.7 ⚠️
    oopsy: $15.2 ✅
```

### Top Available Players

```
🏆 Top 20 Available Players:
--------------------------------------------------
    player_name team position  best_projection  avg_projection
0   Aaron Judge  NYY       OF             42.1            38.7
1  Juan Soto     NYM       OF             41.3            37.9
2  Shohei Ohtani LAD      OF/P            40.8            39.2
```

## 🔮 Future Enhancements

- [ ] Web scraping for NFBC ADP and CloserMonkey data
- [ ] Real-time injury updates
- [ ] Historical performance trends
- [ ] Custom scoring system support
- [ ] Web interface
- [ ] Trade analysis tools

## 🐛 Troubleshooting

### Common Issues

1. **API Rate Limiting**: If you hit Fangraphs rate limits, use cached data or wait
2. **Missing CSV Files**: The tool will warn about missing files but continue with available data
3. **Player Name Mismatches**: Some manual cleanup may be needed for player name consistency

### Getting Help

1. Check the error message for specific issues
2. Ensure you have required Python packages installed
3. Verify your internet connection for API calls
4. Check that CSV files are properly formatted if using manual data
