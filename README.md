# NHK Easy News with WaniKani Integration

A GitHub Pages site that scrapes [NHK News Web Easy](https://news.web.nhk/news/easy/) and displays articles with selective furigana based on your WaniKani kanji progress.

See https://basjacobs93.github.io/nhk-web-easy/.

## Features

- **Automated Daily Scraping**: GitHub Actions automatically scrapes new articles daily
- **WaniKani Integration**: Shows furigana only for kanji you haven't learned yet
- **Interactive Toggles**: Switch between showing unknown kanji furigana, all furigana, or no furigana
- **Mobile Responsive**: Clean, readable design that works on all devices
- **Keyboard Shortcuts**: Press 'F' to toggle unknown kanji furigana, 'A' for all furigana
- **Article Statistics**: See how many kanji you know vs. unknown in each article

## Setup

### 1. Fork and Enable GitHub Pages

1. Fork this repository
2. Go to Settings > Pages
3. Set Source to "GitHub Actions"

### 2. Add WaniKani Integration

1. Get your API token from [WaniKani Settings](https://www.wanikani.com/settings/personal_access_tokens)
2. Go to your repository Settings > Secrets and variables > Actions
3. Create a new secret:
   - Name: `WANIKANI_API_TOKEN`
   - Value: Your WaniKani API token

### 3. Run the Workflow

1. Go to the Actions tab
2. Click "Scrape NHK Easy News and Deploy to GitHub Pages"
3. Click "Run workflow"

Your site will be available at `https://yourusername.github.io/nhkeasier/`

## Local Development

```bash
uv sync
uv run playwright install chromium
export WANIKANI_API_TOKEN="your_token_here"
uv run python src/main.py
```

## How It Works

1. **NHK Authentication**: Automatically accepts NHK terms of service and obtains authentication token
2. **WaniKani Data**: Fetches your kanji learning progress via the WaniKani API
3. **Article Scraping**: Scrapes latest articles from NHK News Web Easy
4. **Furigana Processing**: Analyzes each article's kanji and adds furigana only for unknown kanji
5. **Site Generation**: Creates a static HTML site with interactive furigana toggles
6. **Deployment**: Publishes to GitHub Pages

## File Structure

```
├── .github/workflows/scrape-and-deploy.yml
├── src/
│   ├── main.py
│   ├── auth.py
│   ├── scraper.py
│   ├── wanikani.py
│   ├── furigana_processor.py
│   └── site_generator.py
├── docs/
├── data/
├── config.yml
└── pyproject.toml
```

## License

MIT License - see LICENSE file for details.
