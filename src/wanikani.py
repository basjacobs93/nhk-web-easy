import requests
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import os


class WaniKaniAPI:
    def __init__(self, api_token=None, config_path="config.yml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.api_base = self.config["wanikani"]["api_base"]
        self.cache_duration = self.config["wanikani"]["cache_duration"]

        # Get API token from environment variable or parameter
        self.api_token = api_token or os.getenv("WANIKANI_API_TOKEN")
        if not self.api_token:
            raise ValueError("WaniKani API token is required. Set WANIKANI_API_TOKEN environment variable.")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, endpoint):
        """Get cache file path for an endpoint"""
        import hashlib

        # For very long URLs, use a hash to keep filename short
        if len(endpoint) > 100:
            hash_obj = hashlib.md5(endpoint.encode('utf-8'))
            safe_endpoint = f"cache_{hash_obj.hexdigest()}"
        else:
            safe_endpoint = endpoint.replace("/", "_").replace("?", "_").replace("&", "_")

        return self.cache_dir / f"{safe_endpoint}.json"

    def _is_cache_valid(self, cache_path):
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            cached_time = datetime.fromisoformat(cache_data["cached_at"])
            expiry_time = cached_time + timedelta(seconds=self.cache_duration)

            return datetime.now() < expiry_time
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def _save_to_cache(self, endpoint, data):
        """Save data to cache"""
        cache_path = self._get_cache_path(endpoint)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "data": data
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def _load_from_cache(self, endpoint):
        """Load data from cache"""
        cache_path = self._get_cache_path(endpoint)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            return cache_data["data"]
        except (json.JSONDecodeError, KeyError):
            return None

    def _make_request(self, endpoint, params=None):
        """Make API request with caching"""
        # Check cache first
        cache_key = endpoint
        if params:
            cache_key += "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            print(f"Using cached data for {endpoint}")
            return cached_data

        # Make API request
        url = f"{self.api_base}/{endpoint.lstrip('/')}"

        try:
            print(f"Making API request to {endpoint}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()

            # Save to cache
            self._save_to_cache(cache_key, data)

            return data

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def get_user_info(self):
        """Get user information"""
        return self._make_request("user")

    def get_kanji_assignments(self):
        """Get all kanji assignments for the user"""
        all_assignments = []
        endpoint = "assignments"
        params = {
            "subject_types": "kanji",
            "unlocked": "true"
        }

        while endpoint:
            data = self._make_request(endpoint, params)
            if not data:
                break

            all_assignments.extend(data.get("data", []))

            # Check for pagination
            next_url = data.get("pages", {}).get("next_url")
            if next_url:
                # Extract endpoint from next_url
                endpoint = next_url.replace(self.api_base, "").lstrip("/")
                params = None  # Parameters are included in the URL
            else:
                endpoint = None

        return all_assignments

    def get_kanji_subjects(self, subject_ids=None):
        """Get kanji subject details"""
        if not subject_ids:
            # No specific IDs, get all kanji
            return self._get_all_kanji_subjects()

        # Chunk large requests to avoid filename length issues
        chunk_size = 100  # API can handle ~100 IDs per request
        all_subjects = []

        for i in range(0, len(subject_ids), chunk_size):
            chunk = subject_ids[i:i + chunk_size]
            endpoint = "subjects"
            params = {
                "types": "kanji",
                "ids": ",".join(map(str, chunk))
            }

            print(f"Fetching kanji subjects chunk {i//chunk_size + 1}/{(len(subject_ids) + chunk_size - 1)//chunk_size}")

            while endpoint:
                data = self._make_request(endpoint, params)
                if not data:
                    break

                all_subjects.extend(data.get("data", []))

                # Check for pagination
                next_url = data.get("pages", {}).get("next_url")
                if next_url:
                    endpoint = next_url.replace(self.api_base, "").lstrip("/")
                    params = None
                else:
                    endpoint = None

        return all_subjects

    def _get_all_kanji_subjects(self):
        """Get all kanji subjects without specific IDs"""
        endpoint = "subjects"
        params = {"types": "kanji"}
        all_subjects = []

        while endpoint:
            data = self._make_request(endpoint, params)
            if not data:
                break

            all_subjects.extend(data.get("data", []))

            # Check for pagination
            next_url = data.get("pages", {}).get("next_url")
            if next_url:
                endpoint = next_url.replace(self.api_base, "").lstrip("/")
                params = None
            else:
                endpoint = None

        return all_subjects

    def get_learned_kanji(self):
        """Get all kanji that the user has learned or is currently learning"""
        print("Fetching kanji assignments...")
        assignments = self.get_kanji_assignments()

        if not assignments:
            print("No kanji assignments found")
            return set()

        # Get subject IDs for learned/learning kanji
        learned_subject_ids = []
        for assignment in assignments:
            # Include kanji that are unlocked and have been started
            if assignment.get("data", {}).get("unlocked_at"):
                learned_subject_ids.append(assignment["data"]["subject_id"])

        if not learned_subject_ids:
            print("No learned kanji found")
            return set()

        print(f"Fetching details for {len(learned_subject_ids)} kanji...")
        subjects = self.get_kanji_subjects(learned_subject_ids)

        # Extract kanji characters
        learned_kanji = set()
        for subject in subjects:
            kanji_char = subject.get("data", {}).get("characters")
            if kanji_char:
                learned_kanji.add(kanji_char)

        print(f"Found {len(learned_kanji)} learned kanji")
        return learned_kanji

    def save_learned_kanji(self, output_file="data/learned_kanji.json"):
        """Save learned kanji to file"""
        learned_kanji = self.get_learned_kanji()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        kanji_data = {
            "updated_at": datetime.now().isoformat(),
            "kanji_count": len(learned_kanji),
            "kanji": list(learned_kanji)
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(kanji_data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(learned_kanji)} learned kanji to {output_path}")
        return learned_kanji


if __name__ == "__main__":
    try:
        wk = WaniKaniAPI()
        wk.save_learned_kanji()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the WANIKANI_API_TOKEN environment variable.")