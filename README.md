# NHK Easy News with WaniKani Integration

A GitHub Pages site that scrapes [NHK News Web Easy](https://www3.nhk.or.jp/news/easy/) and displays articles with selective furigana based on your WaniKani kanji progress.

## Features

- **Automated Daily Scraping**: GitHub Actions automatically scrapes new articles daily
- **WaniKani Integration**: Shows furigana only for kanji you haven't learned yet
- **Interactive Toggles**: Switch between showing unknown kanji furigana, all furigana, or no furigana
- **Mobile Responsive**: Clean, readable design that works on all devices
- **Keyboard Shortcuts**: Press 'F' to toggle unknown kanji furigana, 'A' for all furigana
- **Article Statistics**: See how many kanji you know vs. unknown in each article

## Setup

### 1. Repository Setup

1. Fork or clone this repository
2. Enable GitHub Pages in repository settings:
   - Go to Settings > Pages
   - Set Source to "GitHub Actions"

### 2. WaniKani API Token

1. Get your WaniKani API token:
   - Go to [WaniKani Settings > API Tokens](https://www.wanikani.com/settings/personal_access_tokens)
   - Generate a new token with read permissions

2. Add the token to GitHub secrets:
   - Go to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `WANIKANI_API_TOKEN`
   - Value: Your WaniKani API token

### 3. Manual First Run

Trigger the workflow manually for the first time:
- Go to Actions tab
- Click on "Scrape NHK Easy News and Deploy to GitHub Pages"
- Click "Run workflow"

## Local Development

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/nhkeasier.git
cd nhkeasier

# Install dependencies
uv venv
uv pip install -r requirements.txt

# Set up environment variable
export WANIKANI_API_TOKEN="your_token_here"

# Run the pipeline
source .venv/bin/activate
cd src
python main.py
```

### Configuration

Edit `config.yml` to customize:

- `scraper.max_articles`: Number of articles to scrape (default: 20)
- `scraper.timeout`: Request timeout in seconds
- `wanikani.cache_duration`: How long to cache WaniKani data (seconds)
- `site.title`: Website title
- `site.description`: Website description

## How It Works

### Pipeline Steps

1. **WaniKani Data**: Fetches your kanji learning progress via the WaniKani API
2. **Article Scraping**: Scrapes latest articles from NHK News Web Easy
3. **Furigana Processing**: Analyzes each article's kanji and adds furigana only for unknown kanji
4. **Site Generation**: Creates a static HTML site with interactive furigana toggles
5. **Deployment**: Publishes to GitHub Pages

### File Structure

```
├── .github/workflows/
│   └── scrape-and-deploy.yml    # GitHub Actions workflow
├── src/
│   ├── main.py                  # Main pipeline orchestrator
│   ├── scraper.py              # NHK Easy News scraper
│   ├── wanikani.py             # WaniKani API integration
│   ├── furigana_processor.py   # Selective furigana processing
│   └── site_generator.py       # Static site generator
├── docs/                       # Generated GitHub Pages site
├── data/                       # Scraped and processed data
├── config.yml                  # Configuration
├── pyproject.toml             # Python dependencies
└── requirements.txt           # Dependency list for GitHub Actions
```

## Furigana Display Logic

- **Unknown Kanji** (default): Shows furigana only for kanji you haven't learned in WaniKani
- **All Furigana**: Shows furigana for all kanji
- **No Furigana**: Hides all furigana

The system uses your WaniKani assignment data to determine which kanji you've learned. Kanji that are unlocked and have been started are considered "learned."

## Customization

### Styling

Edit `src/site_generator.py` in the `generate_css()` method to customize the appearance.

### Scraping

Modify `src/scraper.py` to adjust:
- CSS selectors for different article elements
- Number of articles to scrape
- Article filtering logic

### Furigana Logic

Adjust `src/furigana_processor.py` to change:
- Which kanji are considered "learned"
- Furigana generation rules
- Text processing logic

## Troubleshooting

### No Articles Appearing

1. Check GitHub Actions logs for scraping errors
2. The NHK Easy News site structure may have changed - update CSS selectors in `scraper.py`
3. Verify the workflow ran successfully

### WaniKani Integration Issues

1. Verify your API token is correctly set in GitHub secrets
2. Check that the token has read permissions
3. WaniKani API rate limits may cause temporary failures

### Site Not Updating

1. Check that GitHub Pages is enabled and set to "GitHub Actions"
2. Verify the workflow completed successfully
3. GitHub Pages deployment can take a few minutes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [NHK News Web Easy](https://www3.nhk.or.jp/news/easy/) for providing accessible Japanese news
- [WaniKani](https://www.wanikani.com/) for kanji learning progress tracking
- [pykakasi](https://github.com/miurahr/pykakasi) for furigana generation