"""Image helper functions for the dashboard."""

import logging
from pathlib import Path

from .reconnection import load_saved_image

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "custom_image.txt"


def save_uploaded_image(image_data: str) -> bool:
    """Persist ``image_data`` to :mod:`data/custom_image.txt`."""

    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w") as fh:
            fh.write(image_data)
        logger.info("Custom image saved successfully")
        return True
    except Exception as exc:  # pragma: no cover - rely on filesystem
        logger.error("Error saving custom image: %s", exc)
        return False


__all__ = ["load_saved_image", "save_uploaded_image"]
