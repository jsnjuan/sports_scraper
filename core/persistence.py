import json
from pathlib import Path


def _category_folder(event_config):
    path = (
        Path("data")
        / event_config["site"]
        / event_config["event_slug"]
        / event_config["distance"]
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pages_folder(event_config):
    pages = _category_folder(event_config) / "pages"
    pages.mkdir(exist_ok=True)
    return pages


def metadata_path(event_config):
    return _category_folder(event_config) / "metadata.json"


def load_metadata(event_config):
    path = metadata_path(event_config)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_metadata(event_config, metadata):
    path = metadata_path(event_config)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def save_page(event_config, page_number, records):
    pages_folder = _pages_folder(event_config)
    file_path = pages_folder / f"page_{page_number}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
