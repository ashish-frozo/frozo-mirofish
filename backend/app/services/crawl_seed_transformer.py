"""
CrawlSeedTransformer — converts a BettaFish crawl bundle into
MiroFish-compatible inputs: seed document, entity hints, calibration data.
"""
from typing import Any, Dict, List
from ..utils.logger import get_logger

logger = get_logger('mirofish.crawl_seed_transformer')


class CrawlSeedTransformer:
    """Transforms a BettaFish crawl bundle into MiroFish prediction inputs."""

    def transform(self, crawl_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a crawl bundle into prediction inputs.

        Args:
            crawl_bundle: The full crawl bundle from BettaFish.

        Returns:
            Dict with keys:
                - seed_text: str — markdown document for ontology generation
                - simulation_requirement: str — what to predict
                - entity_hints: list — pre-extracted entity names/types
                - calibration_data: list — real sentiment data for profile calibration
        """
        seed_text = crawl_bundle.get("seed_document", "")
        simulation_requirement = crawl_bundle.get(
            "simulation_requirement",
            "Predict how public opinion will evolve over the next 72 hours"
        )

        structured = crawl_bundle.get("structured_data", {})
        entities = structured.get("entities", [])

        entity_hints = self._extract_entity_hints(entities)
        calibration_data = self._extract_calibration_data(entities)

        logger.info(
            f"Transformed crawl bundle: {len(seed_text)} chars seed, "
            f"{len(entity_hints)} entity hints, {len(calibration_data)} calibration entries"
        )

        return {
            "seed_text": seed_text,
            "simulation_requirement": simulation_requirement,
            "entity_hints": entity_hints,
            "calibration_data": calibration_data,
            "source_bundle": crawl_bundle,
        }

    def _extract_entity_hints(self, entities: List[Dict]) -> List[Dict[str, str]]:
        """Extract entity name/type pairs to hint ontology generation."""
        hints = []
        for e in entities:
            hints.append({
                "name": e.get("name", ""),
                "type": e.get("type", "PERSON"),
            })
        return hints

    def _extract_calibration_data(self, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Extract real-world sentiment and engagement data for profile calibration."""
        calibration = []
        for e in entities:
            calibration.append({
                "name": e.get("name", ""),
                "type": e.get("type", "PERSON"),
                "sentiment_score": e.get("sentiment_score", 0.0),
                "stance": e.get("stance", "neutral"),
                "post_count": e.get("post_count", 0),
                "avg_engagement": e.get("avg_engagement", 0),
                "influence_score": e.get("influence_score", 0.0),
                "sample_content": e.get("sample_content", []),
            })
        return calibration
