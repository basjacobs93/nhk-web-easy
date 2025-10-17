import json
from pathlib import Path


class WaniKaniLevels:
    def __init__(self, data_path="data/kanji-wanikani.json"):
        self.data_path = Path(data_path)
        self.kanji_by_level = {}
        self.kanji_to_level = {}
        self._load_data()

    def _load_data(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for kanji, info in data.items():
            level = info.get("wk_level")
            if level is None:
                continue

            if level not in self.kanji_by_level:
                self.kanji_by_level[level] = []

            self.kanji_by_level[level].append(kanji)
            self.kanji_to_level[kanji] = level

    def get_kanji_for_level(self, level):
        return self.kanji_by_level.get(level, [])

    def get_all_kanji_up_to_level(self, level):
        kanji_set = set()
        for lvl in range(1, level + 1):
            kanji_set.update(self.kanji_by_level.get(lvl, []))
        return kanji_set

    def get_level_for_kanji(self, kanji):
        return self.kanji_to_level.get(kanji)

    def export_to_js(self, output_path):
        js_content = "const WANIKANI_KANJI = " + json.dumps(self.kanji_by_level, ensure_ascii=False, indent=2) + ";\n\n"
        js_content += "const KANJI_TO_LEVEL = " + json.dumps(self.kanji_to_level, ensure_ascii=False) + ";\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(js_content)

        print(f"Exported WaniKani data to {output_path}")
