import re
import json
from pathlib import Path
from bs4 import BeautifulSoup


class FuriganaProcessor:
    def __init__(self, learned_kanji_file="data/learned_kanji.json"):
        # Load learned kanji
        self.learned_kanji = self._load_learned_kanji(learned_kanji_file)

        # Kanji regex pattern
        self.kanji_pattern = re.compile(r"[\u4e00-\u9faf]+")

    def _load_learned_kanji(self, kanji_file):
        """Load learned kanji from file"""
        kanji_path = Path(kanji_file)

        if not kanji_path.exists():
            print(f"Warning: {kanji_file} not found. No kanji will be marked as learned.")
            return set()

        try:
            with open(kanji_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("kanji", []))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading learned kanji: {e}")
            return set()

    def _contains_unknown_kanji(self, text):
        """Check if text contains any kanji not in learned set"""
        kanji_chars = self.kanji_pattern.findall(text)

        for kanji_group in kanji_chars:
            for kanji in kanji_group:
                if kanji not in self.learned_kanji:
                    return True

        return False

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
                    # Check if this kanji group contains unknown kanji
                    has_unknown = self._contains_unknown_kanji(kanji)

                    segments.append({
                        "type": "furigana" if has_unknown else "kanji",
                        "kanji": kanji,
                        "reading": reading,
                        "unknown": has_unknown
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
        """Convert segments to HTML with toggle functionality"""
        # Create three versions: all furigana, unknown only, no furigana
        known_parts = []      # All furigana (show all)
        unknown_parts = []    # Unknown furigana only (default)
        no_furigana_parts = []  # No furigana

        for segment in segments:
            if segment["type"] == "text":
                # Add text to all containers
                text = segment["content"]
                known_parts.append(text)
                unknown_parts.append(text)
                no_furigana_parts.append(text)

            elif segment["type"] == "html":
                # Preserve HTML tags like <p>, <span>
                html = segment["content"]
                known_parts.append(html)
                unknown_parts.append(html)
                no_furigana_parts.append(html)

            elif segment["type"] == "kanji":
                # Known kanji (has furigana but marked as known)
                kanji = segment["kanji"]
                reading = segment["reading"]

                known_parts.append(f'<ruby>{kanji}<rt>{reading}</rt></ruby>')  # With furigana
                unknown_parts.append(kanji)  # Without furigana
                no_furigana_parts.append(kanji)  # Without furigana

            elif segment["type"] == "furigana":
                # Unknown kanji (has furigana and marked as unknown)
                kanji = segment["kanji"]
                reading = segment["reading"]

                ruby_html = f'<ruby>{kanji}<rt>{reading}</rt></ruby>'
                known_parts.append(ruby_html)  # With furigana
                unknown_parts.append(ruby_html)  # With furigana
                no_furigana_parts.append(kanji)  # Without furigana

        # Create HTML with three versions
        html = f'''<span class="known-version">{"".join(known_parts)}</span><span class="unknown-version">{"".join(unknown_parts)}</span><span class="no-furigana-version">{"".join(no_furigana_parts)}</span>'''

        return html

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

            elif segment["type"] in ["kanji", "furigana"]:
                kanji_text = segment.get("kanji") or segment.get("content", "")
                if char_count + len(kanji_text) <= max_chars:
                    char_count += len(kanji_text)
                    preview_segments.append(segment)
                else:
                    # Don't partially include kanji segments
                    break

        # Generate HTML from the preview segments
        return self.to_html_with_toggle(preview_segments)

    def get_text_stats(self, segments):
        """Get statistics about the text"""
        stats = {
            "total_kanji": 0,
            "unknown_kanji": 0,
            "known_kanji": 0,
            "unique_unknown_kanji": set(),
            "unique_known_kanji": set()
        }

        for segment in segments:
            if segment["type"] in ["kanji", "furigana"]:
                kanji_text = segment.get("kanji", "")

                for kanji in kanji_text:
                    if re.match(r"[\u4e00-\u9faf]", kanji):
                        stats["total_kanji"] += 1

                        if kanji in self.learned_kanji:
                            stats["known_kanji"] += 1
                            stats["unique_known_kanji"].add(kanji)
                        else:
                            stats["unknown_kanji"] += 1
                            stats["unique_unknown_kanji"].add(kanji)

        # Convert sets to lists for JSON serialization
        stats["unique_unknown_kanji"] = list(stats["unique_unknown_kanji"])
        stats["unique_known_kanji"] = list(stats["unique_known_kanji"])

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