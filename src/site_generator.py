import json
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import re


class SiteGenerator:
    def __init__(self, config_path="config.yml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path(self.config["site"]["output_dir"])
        self.site_title = self.config["site"]["title"]
        self.site_description = self.config["site"]["description"]

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_articles(self, articles_file="data/processed_articles.json"):
        """Load processed articles from file"""
        articles_path = Path(articles_file)

        if not articles_path.exists():
            print(f"Warning: {articles_file} not found")
            return []

        try:
            with open(articles_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading articles: {e}")
            return []

    def _create_article_slug(self, title, url):
        """Create a URL-friendly slug for an article"""
        # Extract article ID from URL if possible
        url_match = re.search(r"k10(\d+)", url)
        if url_match:
            return f"article-{url_match.group(1)}"

        # Fallback: create slug from title
        slug = re.sub(r"[^\w\s-]", "", title.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug[:50]  # Limit length

    def generate_index_page(self, articles):
        """Generate the main index page"""
        template_str = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site_title }}</title>
    <meta name="description" content="{{ site_description }}">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1>{{ site_title }}</h1>
            <p class="site-description">{{ site_description }}</p>

            <div class="controls">
                <label class="toggle-label">
                    <input type="checkbox" id="furigana-toggle" checked>
                    <span class="slider"></span>
                    <span class="label-text">未習漢字のフリガナを表示</span>
                </label>

                <label class="toggle-label">
                    <input type="checkbox" id="all-furigana-toggle">
                    <span class="slider"></span>
                    <span class="label-text">全フリガナを表示</span>
                </label>
            </div>
        </div>
    </header>

    <main class="container">
        <section class="articles-list">
            <h2>最新記事</h2>

            {% if articles %}
                <div class="articles-grid">
                    {% for article in articles %}
                    <article class="article-card">
                        <div class="article-header">
                            <h3 class="article-title">
                                <a href="{{ article.slug }}.html">{{ article.title_html|safe }}</a>
                            </h3>
                            {% if article.date %}
                            <time class="article-date">{{ article.date }}</time>
                            {% endif %}
                        </div>

                        {% if article.stats %}
                        <div class="article-stats">
                            <span class="stat">漢字: {{ article.stats.total_kanji }}</span>
                            <span class="stat unknown">未習: {{ article.stats.unknown_kanji }}</span>
                            <span class="stat known">既習: {{ article.stats.known_kanji }}</span>
                        </div>
                        {% endif %}

                        {% if article.local_image_path %}
                        <div class="article-image">
                            <img src="{{ article.local_image_path }}" alt="{{ article.title }}" loading="lazy">
                        </div>
                        {% endif %}

                        <div class="article-preview">
                            {{ article.content_preview_html|safe }}...
                        </div>

                        <div class="article-footer">
                            <a href="{{ article.slug }}.html" class="read-more">続きを読む</a>
                            <a href="{{ article.url }}" target="_blank" class="original-link">元記事</a>
                        </div>
                    </article>
                    {% endfor %}
                </div>
            {% else %}
                <p class="no-articles">記事が見つかりませんでした。</p>
            {% endif %}
        </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>Last updated: {{ current_time }}</p>
            <p>Data from <a href="https://www3.nhk.or.jp/news/easy/" target="_blank">NHK News Web Easy</a></p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""

        template = Template(template_str)

        # Prepare articles with slugs
        for article in articles:
            article["slug"] = self._create_article_slug(article.get("title", ""), article.get("url", ""))

        html = template.render(
            site_title=self.site_title,
            site_description=self.site_description,
            articles=articles,
            current_time=datetime.now().strftime("%Y年%m月%d日 %H:%M")
        )

        index_path = self.output_dir / "index.html"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Generated index page: {index_path}")

    def generate_article_page(self, article):
        """Generate individual article page"""
        template_str = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ article.title }} - {{ site_title }}</title>
    <meta name="description" content="{{ article.title }}">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <nav class="breadcrumb">
                <a href="index.html">{{ site_title }}</a> > <span>記事</span>
            </nav>

            <div class="controls">
                <label class="toggle-label">
                    <input type="checkbox" id="furigana-toggle" checked>
                    <span class="slider"></span>
                    <span class="label-text">未習漢字のフリガナを表示</span>
                </label>

                <label class="toggle-label">
                    <input type="checkbox" id="all-furigana-toggle">
                    <span class="slider"></span>
                    <span class="label-text">全フリガナを表示</span>
                </label>
            </div>
        </div>
    </header>

    <main class="container">
        <article class="article-full">
            <header class="article-header">
                <h1 class="article-title">{{ article.title_html|safe }}</h1>

                {% if article.date %}
                <time class="article-date">{{ article.date }}</time>
                {% endif %}

                {% if article.stats %}
                <div class="article-stats">
                    <span class="stat">漢字: {{ article.stats.total_kanji }}</span>
                    <span class="stat unknown">未習: {{ article.stats.unknown_kanji }}</span>
                    <span class="stat known">既習: {{ article.stats.known_kanji }}</span>
                </div>

                {% if article.stats.unique_unknown_kanji %}
                <details class="unknown-kanji-list">
                    <summary>未習漢字一覧 ({{ article.stats.unique_unknown_kanji|length }}個)</summary>
                    <div class="kanji-grid">
                        {% for kanji in article.stats.unique_unknown_kanji %}
                        <span class="kanji-item">{{ kanji }}</span>
                        {% endfor %}
                    </div>
                </details>
                {% endif %}
                {% endif %}
            </header>

            {% if article.local_image_path %}
            <div class="article-image-full">
                <img src="{{ article.local_image_path }}" alt="{{ article.title }}">
            </div>
            {% endif %}

            <div class="article-content">
                {{ article.content_html|safe }}
            </div>

            <footer class="article-footer">
                <a href="{{ article.url }}" target="_blank" class="original-link">元記事を見る</a>
                <a href="index.html" class="back-link">記事一覧に戻る</a>
            </footer>
        </article>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>Data from <a href="https://www3.nhk.or.jp/news/easy/" target="_blank">NHK News Web Easy</a></p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""

        template = Template(template_str)

        slug = self._create_article_slug(article.get("title", ""), article.get("url", ""))

        html = template.render(
            site_title=self.site_title,
            article=article
        )

        article_path = self.output_dir / f"{slug}.html"
        with open(article_path, "w", encoding="utf-8") as f:
            f.write(html)

        return slug

    def generate_css(self):
        """Generate CSS file"""
        css_content = """/* CSS Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Ensure ruby elements are not affected by reset */
ruby, rt {
    margin: unset;
    padding: unset;
    box-sizing: unset;
}

body {
    font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans CJK JP', sans-serif;
    line-height: 1.7;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.site-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.site-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    text-align: center;
}

.site-description {
    text-align: center;
    font-size: 1.1rem;
    opacity: 0.9;
    margin-bottom: 2rem;
}

.breadcrumb {
    margin-bottom: 1rem;
}

.breadcrumb a {
    color: white;
    text-decoration: none;
}

.breadcrumb a:hover {
    text-decoration: underline;
}

/* Controls */
.controls {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.toggle-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    user-select: none;
}

.toggle-label input[type="checkbox"] {
    display: none;
}

.slider {
    width: 50px;
    height: 25px;
    background: rgba(255,255,255,0.3);
    border-radius: 25px;
    position: relative;
    transition: background 0.3s;
}

.slider:before {
    content: '';
    position: absolute;
    width: 21px;
    height: 21px;
    border-radius: 50%;
    background: white;
    top: 2px;
    left: 2px;
    transition: transform 0.3s;
}

.toggle-label input:checked + .slider {
    background: rgba(255,255,255,0.6);
}

.toggle-label input:checked + .slider:before {
    transform: translateX(25px);
}

.label-text {
    font-size: 0.9rem;
}

/* Articles Grid */
.articles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.article-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.article-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.article-title {
    font-size: 1.3rem;
    margin-bottom: 0.5rem;
}

.article-title a {
    color: #333;
    text-decoration: none;
}

.article-title a:hover {
    color: #667eea;
}

.article-date {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    display: block;
}

/* Article Stats */
.article-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.stat {
    background: #e9ecef;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
}

.stat.unknown {
    background: #fff3cd;
    color: #856404;
}

.stat.known {
    background: #d1ecf1;
    color: #0c5460;
}

/* Article Images */
.article-image {
    margin: 1rem 0;
    border-radius: 8px;
    overflow: hidden;
}

.article-image img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 8px;
    transition: transform 0.2s;
}

.article-image img:hover {
    transform: scale(1.02);
}

.article-image-full {
    margin: 2rem 0;
    text-align: center;
}

.article-image-full img {
    max-width: 100%;
    height: auto;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

/* Article Content */
.article-preview {
    color: #666;
    margin-bottom: 1rem;
    line-height: 1.6;
}

.article-content {
    font-size: 1.1rem;
    line-height: 1.8;
    margin: 2rem 0;
}

.article-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid #e9ecef;
}

.read-more, .original-link, .back-link {
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    transition: background 0.2s;
}

.read-more:hover, .original-link:hover, .back-link:hover {
    background: #f8f9ff;
}

/* Furigana Styles */
ruby {
    ruby-position: over;
}

rt {
    font-size: 0.6em;
    color: #666;
    font-weight: normal;
}

/* Furigana Toggle System */
.known-version, .no-furigana-version {
    display: none;
}

.unknown-version {
    display: inline;
}

/* Hide furigana completely */
body.hide-unknown-furigana .unknown-version {
    display: none;
}

body.hide-unknown-furigana .no-furigana-version {
    display: inline;
}

/* Show all furigana */
body.show-all-furigana .unknown-version {
    display: none;
}

body.show-all-furigana .known-version {
    display: inline;
}

/* Unknown Kanji List */
.unknown-kanji-list {
    margin: 1rem 0;
}

.unknown-kanji-list summary {
    cursor: pointer;
    font-weight: 500;
    color: #667eea;
    margin-bottom: 0.5rem;
}

.kanji-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.kanji-item {
    background: #fff3cd;
    color: #856404;
    padding: 0.5rem;
    text-align: center;
    border-radius: 6px;
    font-weight: 500;
    font-size: 1.2rem;
}

/* Full Article */
.article-full {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.article-full .article-title {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #333;
}

/* Footer */
.site-footer {
    background: #343a40;
    color: white;
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
}

.site-footer a {
    color: #adb5bd;
}

.no-articles {
    text-align: center;
    color: #666;
    font-size: 1.1rem;
    padding: 3rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }

    .site-header h1 {
        font-size: 2rem;
    }

    .articles-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }

    .controls {
        flex-direction: column;
        gap: 1rem;
    }

    .article-footer {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }

    .article-full {
        padding: 1rem;
    }

    .article-full .article-title {
        font-size: 1.5rem;
    }

    .article-image img {
        height: 150px;
    }

    .article-image-full img {
        border-radius: 8px;
    }
}"""

        css_path = self.output_dir / "style.css"
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css_content)

        print(f"Generated CSS: {css_path}")

    def generate_javascript(self):
        """Generate JavaScript file"""
        js_content = """// Furigana toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const furiganaToggle = document.getElementById('furigana-toggle');
    const allFuriganaToggle = document.getElementById('all-furigana-toggle');
    const body = document.body;

    // Load saved preferences
    const showUnknownFurigana = localStorage.getItem('showUnknownFurigana') !== 'false';
    const showAllFurigana = localStorage.getItem('showAllFurigana') === 'true';

    // Set initial states
    furiganaToggle.checked = showUnknownFurigana;
    allFuriganaToggle.checked = showAllFurigana;

    // Apply initial classes
    updateFuriganaDisplay();

    // Event listeners
    furiganaToggle.addEventListener('change', function() {
        localStorage.setItem('showUnknownFurigana', this.checked);
        // If turning off unknown furigana, also turn off all furigana
        if (!this.checked && allFuriganaToggle.checked) {
            allFuriganaToggle.checked = false;
            localStorage.setItem('showAllFurigana', false);
        }
        updateFuriganaDisplay();
    });

    allFuriganaToggle.addEventListener('change', function() {
        localStorage.setItem('showAllFurigana', this.checked);
        // If turning on all furigana, also turn on unknown furigana
        if (this.checked && !furiganaToggle.checked) {
            furiganaToggle.checked = true;
            localStorage.setItem('showUnknownFurigana', true);
        }
        updateFuriganaDisplay();
    });

    function updateFuriganaDisplay() {
        // Remove all furigana classes
        body.classList.remove('hide-unknown-furigana', 'show-all-furigana');

        if (allFuriganaToggle.checked) {
            // Show all furigana (overrides everything)
            body.classList.add('show-all-furigana');
        } else if (furiganaToggle.checked) {
            // Show only unknown kanji furigana (default)
            // No special class needed
        } else {
            // Hide all furigana
            body.classList.add('hide-unknown-furigana');
        }
    }

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add click tracking for external links
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.addEventListener('click', function() {
            // Could add analytics here if needed
            console.log('External link clicked:', this.href);
        });
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // F key: toggle unknown kanji furigana
    if (event.key === 'f' || event.key === 'F') {
        if (!event.ctrlKey && !event.metaKey && !event.altKey) {
            const furiganaToggle = document.getElementById('furigana-toggle');
            if (furiganaToggle && !isInputFocused()) {
                event.preventDefault();
                furiganaToggle.click();
            }
        }
    }

    // A key: toggle all furigana
    if (event.key === 'a' || event.key === 'A') {
        if (!event.ctrlKey && !event.metaKey && !event.altKey) {
            const allFuriganaToggle = document.getElementById('all-furigana-toggle');
            if (allFuriganaToggle && !isInputFocused()) {
                event.preventDefault();
                allFuriganaToggle.click();
            }
        }
    }
});

function isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
    );
}

// Add visual feedback for keyboard shortcuts
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard shortcut hints
    const furiganaToggle = document.querySelector('#furigana-toggle').closest('.toggle-label');
    const allFuriganaToggle = document.querySelector('#all-furigana-toggle').closest('.toggle-label');

    if (furiganaToggle) {
        furiganaToggle.title = 'キーボードショートカット: F';
    }
    if (allFuriganaToggle) {
        allFuriganaToggle.title = 'キーボードショートカット: A';
    }
});"""

        js_path = self.output_dir / "script.js"
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)

        print(f"Generated JavaScript: {js_path}")

    def generate_site(self, articles_file="data/processed_articles.json"):
        """Generate the complete static site"""
        print("Loading articles...")
        articles = self._load_articles(articles_file)

        if not articles:
            print("No articles found. Generating empty site.")

        print("Generating index page...")
        self.generate_index_page(articles)

        print("Generating individual article pages...")
        for article in articles:
            slug = self.generate_article_page(article)
            print(f"  Generated: {slug}.html")

        print("Generating CSS...")
        self.generate_css()

        print("Generating JavaScript...")
        self.generate_javascript()

        print(f"Site generated successfully in {self.output_dir}")
        print(f"Total articles: {len(articles)}")


if __name__ == "__main__":
    generator = SiteGenerator()
    generator.generate_site()