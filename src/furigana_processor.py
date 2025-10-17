import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from wanikani_levels import WaniKaniLevels


class FuriganaProcessor:
    def __init__(self, wanikani_data_path="data/kanji-wanikani.json"):
        # Load WaniKani level data
        self.wk_levels = WaniKaniLevels(wanikani_data_path)

        # Kanji regex pattern
        self.kanji_pattern = re.compile(r"[\u4e00-\u9faf]+")

    def _get_max_kanji_level(self, text):
        """Get the maximum WaniKani level among all kanji in text"""
        kanji_chars = self.kanji_pattern.findall(text)
        max_level = 0

        for kanji_group in kanji_chars:
            for kanji in kanji_group:
                level = self.wk_levels.get_level_for_kanji(kanji)
                if level and level > max_level:
                    max_level = level

        return max_level

    def _parse_ruby_html(self, html_text):
        """Parse HTML with ruby tags and extract segments"""
        if not html_text:
            return []

        soup = BeautifulSoup(html_text, "html.parser")
        segments = []

        # Get the root element or body
        root = soup.body if soup.body else soup

        # Process direct children recursively
        def process_element(element, preserve_tags=None):
            if preserve_tags is None:
                preserve_tags = {"p", "div", "br"}

            if element.name == "ruby":
                # Extract kanji and reading from ruby tag
                kanji = ""
                reading = ""

                for child in element.children:
                    if child.name == "rt":
                        reading = child.get_text()
                    elif child.name is None:  # Text node
                        kanji += str(child)

                if kanji and reading:
                    # Get the maximum WaniKani level for this kanji group
                    max_level = self._get_max_kanji_level(kanji)

                    segments.append({
                        "type": "kanji",
                        "kanji": kanji,
                        "reading": reading,
                        "level": max_level
                    })
            elif element.name is None:
                # Text node
                text = str(element)
                if text:
                    segments.append({
                        "type": "text",
                        "content": text
                    })
            elif element.name in preserve_tags:
                # Preserve paragraph/div structure
                if element.name == "br":
                    segments.append({
                        "type": "html",
                        "content": "<br>"
                    })
                else:
                    # Opening tag
                    segments.append({
                        "type": "html",
                        "content": f"<{element.name}>"
                    })
                    # Process children
                    for child in element.children:
                        process_element(child, preserve_tags)
                    # Closing tag
                    segments.append({
                        "type": "html",
                        "content": f"</{element.name}>"
                    })
            else:
                # Other HTML element - process its children without preserving the tag
                for child in element.children:
                    process_element(child, preserve_tags)

        # Start processing from root
        for child in root.children:
            process_element(child)

        return segments

    def process_text(self, text):
        """Process text and return segments with furigana annotations"""
        if not text:
            return []

        # Parse HTML to extract ruby tags
        return self._parse_ruby_html(text)


    def to_html_with_toggle(self, segments):
        """Convert segments to HTML with level-based furigana control"""
        parts = []

        for segment in segments:
            if segment["type"] == "text":
                parts.append(segment["content"])

            elif segment["type"] == "html":
                parts.append(segment["content"])

            elif segment["type"] == "kanji":
                kanji = segment["kanji"]
                reading = segment["reading"]
                level = segment.get("level", 0)

                # Create ruby tag with data-level attribute for JavaScript control
                if level > 0:
                    parts.append(f'<ruby data-level="{level}">{kanji}<rt>{reading}</rt></ruby>')
                else:
                    # Kanji not in WaniKani system, always show furigana
                    parts.append(f'<ruby data-level="unknown">{kanji}<rt>{reading}</rt></ruby>')

        return "".join(parts)

    def create_preview_html(self, segments, max_chars=200):
        """Create a truncated preview that preserves HTML structure"""
        # First get the plain text length to determine where to cut
        plain_text = ""
        char_count = 0
        preview_segments = []

        for segment in segments:
            if segment["type"] == "text":
                text = segment["content"]
                if char_count + len(text) <= max_chars:
                    plain_text += text
                    char_count += len(text)
                    preview_segments.append(segment)
                else:
                    # Truncate this segment
                    remaining = max_chars - char_count
                    truncated_text = text[:remaining]
                    plain_text += truncated_text
                    preview_segments.append({
                        "type": "text",
                        "content": truncated_text
                    })
                    break

            elif segment["type"] == "kanji":
                kanji_text = segment.get("kanji", "")
                if char_count + len(kanji_text) <= max_chars:
                    char_count += len(kanji_text)
                    preview_segments.append(segment)
                else:
                    # Don't partially include kanji segments
                    break

        # Generate HTML from the preview segments
        return self.to_html_with_toggle(preview_segments)

    def get_text_stats(self, segments):
        """Get statistics about kanji by level"""
        stats = {
            "total_kanji": 0,
            "kanji_by_level": {},
            "unique_kanji_by_level": {}
        }

        for segment in segments:
            if segment["type"] == "kanji":
                kanji_text = segment.get("kanji", "")
                segment_level = segment.get("level", 0)

                for kanji in kanji_text:
                    if re.match(r"[\u4e00-\u9faf]", kanji):
                        stats["total_kanji"] += 1
                        level = self.wk_levels.get_level_for_kanji(kanji) or 0

                        if level not in stats["kanji_by_level"]:
                            stats["kanji_by_level"][level] = 0
                            stats["unique_kanji_by_level"][level] = set()

                        stats["kanji_by_level"][level] += 1
                        stats["unique_kanji_by_level"][level].add(kanji)

        # Convert sets to lists for JSON serialization
        for level in stats["unique_kanji_by_level"]:
            stats["unique_kanji_by_level"][level] = list(stats["unique_kanji_by_level"][level])

        return stats

    def process_article(self, article):
        """Process an entire article and return enhanced data"""
        processed_article = article.copy()

        # Process title - use title_with_ruby if available, otherwise fall back to title
        title_source = article.get("title_with_ruby") or article.get("title", "")
        if title_source:
            title_segments = self.process_text(title_source)
            processed_article["title_segments"] = title_segments
            processed_article["title_html"] = self.to_html_with_toggle(title_segments)

        # Process content - use raw_html body if available
        if article.get("raw_html"):
            # Extract article body from raw HTML
            soup = BeautifulSoup(article["raw_html"], "html.parser")
            body_elem = soup.select_one("#js-article-body")
            if body_elem:
                content_html = str(body_elem)
                content_segments = self.process_text(content_html)
                processed_article["content_segments"] = content_segments
                processed_article["content_html"] = self.to_html_with_toggle(content_segments)
                processed_article["content_preview_html"] = self.create_preview_html(content_segments, 200)

                # Add statistics
                processed_article["stats"] = self.get_text_stats(content_segments)
        elif article.get("content"):
            # Fallback to plain content if raw_html not available
            content_segments = self.process_text(article["content"])
            processed_article["content_segments"] = content_segments
            processed_article["content_html"] = self.to_html_with_toggle(content_segments)
            processed_article["content_preview_html"] = self.create_preview_html(content_segments, 200)

            # Add statistics
            processed_article["stats"] = self.get_text_stats(content_segments)

        return processed_article


if __name__ == "__main__":
    # Test the processor
    processor = FuriganaProcessor()

    test_text = "インフルエンザ　<ruby>去年<rt>きょねん</rt></ruby>より5<ruby>週間<rt>しゅうかん</rt></ruby><ruby>早<rt>はや</rt></ruby>く「<ruby>流行<rt>りゅうこう</rt></ruby>」"
    segments = processor.process_text(test_text)

    print("Segments:")
    for segment in segments:
        print(f"  {segment}")

    print(f"\nHTML: {processor.to_html_with_toggle(segments)}")
    print(f"\nStats: {processor.get_text_stats(segments)}")