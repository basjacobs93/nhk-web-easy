#!/usr/bin/env python3

import json
from pathlib import Path
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper import NHKEasyScraper
from wanikani import WaniKaniAPI
from furigana_processor import FuriganaProcessor
from site_generator import SiteGenerator


def main():
    """Main pipeline to scrape, process, and generate the site"""
    print("=== NHK Easy News Pipeline ===")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    try:
        # Step 1: Fetch WaniKani data
        print("\n1. Fetching WaniKani kanji data...")
        wk_api = WaniKaniAPI()
        learned_kanji = wk_api.save_learned_kanji("data/learned_kanji.json")
        print(f"   Found {len(learned_kanji)} learned kanji")

    except Exception as e:
        print(f"   Warning: WaniKani API failed: {e}")
        print("   Continuing without WaniKani data...")

    try:
        # Step 2: Scrape NHK Easy News
        print("\n2. Scraping NHK Easy News...")
        scraper = NHKEasyScraper()
        articles = scraper.scrape_all()

        if not articles:
            print("   No articles scraped. Exiting.")
            return

        # Save raw articles
        scraper.save_articles(articles, "data/articles.json")

    except Exception as e:
        print(f"   Error scraping articles: {e}")
        return

    try:
        # Step 3: Process articles with furigana
        print("\n3. Processing articles with furigana...")
        processor = FuriganaProcessor("data/learned_kanji.json")

        processed_articles = []
        for i, article in enumerate(articles, 1):
            print(f"   Processing article {i}/{len(articles)}: {article.get('title', 'Untitled')[:50]}...")

            try:
                processed_article = processor.process_article(article)
                processed_articles.append(processed_article)

                # Print stats
                stats = processed_article.get("stats", {})
                if stats:
                    print(f"     漢字: {stats.get('total_kanji', 0)}, "
                          f"未習: {stats.get('unknown_kanji', 0)}, "
                          f"既習: {stats.get('known_kanji', 0)}")

            except Exception as e:
                print(f"     Error processing article: {e}")
                continue

        # Save processed articles
        processed_path = "data/processed_articles.json"
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump(processed_articles, f, ensure_ascii=False, indent=2)

        print(f"   Saved {len(processed_articles)} processed articles to {processed_path}")

    except Exception as e:
        print(f"   Error processing articles: {e}")
        return

    try:
        # Step 4: Generate static site
        print("\n4. Generating static site...")
        generator = SiteGenerator()
        generator.generate_site("data/processed_articles.json")

        print("\n=== Pipeline completed successfully! ===")
        print(f"Site generated in: {generator.output_dir}")
        print("You can now deploy the 'docs' directory to GitHub Pages.")

    except Exception as e:
        print(f"   Error generating site: {e}")
        return


if __name__ == "__main__":
    main()