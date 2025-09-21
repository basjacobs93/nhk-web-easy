import re
import json
from pathlib import Path
import pykakasi


class FuriganaProcessor:
    def __init__(self, learned_kanji_file="data/learned_kanji.json"):
        # Initialize kakasi for reading conversion
        self.kakasi = pykakasi.kakasi()

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

    def _get_reading(self, text):
        """Get hiragana reading for text using pykakasi"""
        try:
            result = self.kakasi.convert(text)
            reading = "".join([item["hira"] for item in result])
            return reading
        except Exception as e:
            print(f"Error converting {text} to hiragana: {e}")
            return ""

    def _split_text_with_furigana(self, text):
        """Split text into segments and add furigana where needed"""
        segments = []
        last_end = 0

        # Find all kanji sequences
        for match in self.kanji_pattern.finditer(text):
            start, end = match.span()
            kanji_text = match.group()

            # Add text before kanji (if any)
            if start > last_end:
                before_text = text[last_end:start]
                segments.append({
                    "type": "text",
                    "content": before_text
                })

            # Check if this kanji group needs furigana
            needs_furigana = self._contains_unknown_kanji(kanji_text)

            if needs_furigana:
                reading = self._get_reading(kanji_text)
                segments.append({
                    "type": "furigana",
                    "kanji": kanji_text,
                    "reading": reading,
                    "unknown": True
                })
            else:
                segments.append({
                    "type": "kanji",
                    "content": kanji_text,
                    "unknown": False
                })

            last_end = end

        # Add remaining text (if any)
        if last_end < len(text):
            remaining_text = text[last_end:]
            segments.append({
                "type": "text",
                "content": remaining_text
            })

        return segments

    def process_text(self, text):
        """Process text and return segments with furigana annotations"""
        if not text:
            return []

        # Split text into sentences for better processing
        sentences = re.split(r"([。！？\n])", text)
        all_segments = []

        for sentence in sentences:
            if sentence.strip():
                segments = self._split_text_with_furigana(sentence)
                all_segments.extend(segments)

        return all_segments


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

            elif segment["type"] == "kanji":
                # Known kanji
                kanji = segment["content"]
                reading = self._get_reading(kanji)

                known_parts.append(f'<ruby>{kanji}<rt>{reading}</rt></ruby>')  # With furigana
                unknown_parts.append(kanji)  # Without furigana
                no_furigana_parts.append(kanji)  # Without furigana

            elif segment["type"] == "furigana":
                # Unknown kanji
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
                kanji_text = segment.get("kanji") or segment.get("content", "")

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

        # Process title
        if article.get("title"):
            title_segments = self.process_text(article["title"])
            processed_article["title_segments"] = title_segments
            processed_article["title_html"] = self.to_html_with_toggle(title_segments)

        # Process content
        if article.get("content"):
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

    test_text = "今日は良い天気です。学校に行きます。"
    segments = processor.process_text(test_text)

    print("Segments:")
    for segment in segments:
        print(f"  {segment}")

    print(f"\nHTML: {processor.to_html_with_toggle(segments)}")
    print(f"\nStats: {processor.get_text_stats(segments)}")