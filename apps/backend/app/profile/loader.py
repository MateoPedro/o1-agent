from pathlib import Path
import yaml

PROFILE_PATH = Path(__file__).parent.parent.parent / "profile.yaml"


def load_profile() -> dict:
    with open(PROFILE_PATH) as f:
        return yaml.safe_load(f)


def get_bio(variant: str = "short") -> str:
    """variant: short | medium | full"""
    profile = load_profile()
    return profile["bio"][variant]


def get_story_module(name: str) -> dict:
    profile = load_profile()
    return profile["story_modules"][name]


def get_talk_topic_seeds() -> list[str]:
    profile = load_profile()
    return profile["talk_topic_seeds"]
