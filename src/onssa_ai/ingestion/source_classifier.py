"""Classify downloaded ONSSA sources for corpus construction."""

from onssa_ai.ingestion.models import SourceClassification
from onssa_ai.ingestion.taxonomy import SiteTaxonomy
from onssa_ai.sources.models import SourceManifestEntry


class SourceClassifier:
    """Assign domain/subdomain metadata from ONSSA website hierarchy."""

    def __init__(
        self,
        include_all_sources: bool = False,
        target_vertical: str = "regulation",
        target_domain: str = "reglementation_transversale",
        target_subdomain: str = "securite_sanitaire",
        taxonomy: SiteTaxonomy | None = None,
    ) -> None:
        self.include_all_sources = include_all_sources
        self.target_vertical = target_vertical
        self.target_domain = target_domain
        self.target_subdomain = target_subdomain
        self.taxonomy = taxonomy

    def classify(self, entry: SourceManifestEntry) -> SourceClassification:
        text = " ".join(
            value or ""
            for value in [
                entry.url,
                entry.title,
                entry.parent_url,
                entry.local_path,
            ]
        ).lower()

        language = "ar" if "lang=ar" in text or "_ar" in text else "fr"
        regulation_type = self._regulation_type(text)
        matched_keywords = self._food_safety_keywords(text)
        taxonomy_match = self.taxonomy.match(entry.url, entry.parent_url) if self.taxonomy else None

        if entry.kind != "pdf":
            return self._excluded(language, regulation_type, "non-PDF source")

        if taxonomy_match and taxonomy_match.include_in_first_slice:
            return SourceClassification(
                include=True,
                vertical=taxonomy_match.vertical,
                domain=taxonomy_match.domain,
                subdomain=taxonomy_match.subdomain,
                language=language,
                regulation_type=regulation_type,
                confidence="high",
                matched_keywords=matched_keywords,
                needs_review=False,
                site_hierarchy=taxonomy_match.display_path,
                site_parent_url=entry.parent_url,
                site_matched_rule=taxonomy_match.matched_rule,
                site_sub_subdomain=taxonomy_match.sub_subdomain,
                site_sub_subdomain_display=taxonomy_match.sub_subdomain_display,
                reason="matched ONSSA site taxonomy first slice",
            )

        if self.include_all_sources:
            if taxonomy_match and taxonomy_match.matched:
                return SourceClassification(
                    include=True,
                    vertical=taxonomy_match.vertical,
                    domain=taxonomy_match.domain,
                    subdomain=taxonomy_match.subdomain,
                    language=language,
                    regulation_type=regulation_type,
                    confidence="high",
                    matched_keywords=matched_keywords,
                    needs_review=False,
                    site_hierarchy=taxonomy_match.display_path,
                    site_parent_url=entry.parent_url,
                    site_matched_rule=taxonomy_match.matched_rule,
                    site_sub_subdomain=taxonomy_match.sub_subdomain,
                    site_sub_subdomain_display=taxonomy_match.sub_subdomain_display,
                    reason="matched ONSSA site taxonomy broad corpus",
                )
            return SourceClassification(
                include=True,
                vertical=self.target_vertical,
                domain="unclassified",
                subdomain="unclassified",
                language=language,
                regulation_type=regulation_type,
                confidence="low",
                matched_keywords=matched_keywords,
                needs_review=True,
                site_parent_url=entry.parent_url,
                reason="included for broad corpus but no ONSSA taxonomy rule matched",
            )

        return self._excluded(language, regulation_type, "outside configured first slice")

    def _excluded(
        self,
        language: str,
        regulation_type: str | None,
        reason: str,
    ) -> SourceClassification:
        return SourceClassification(
            include=False,
            vertical=self.target_vertical,
            domain="unclassified",
            subdomain="unclassified",
            language=language,
            regulation_type=regulation_type,
            confidence="low",
            matched_keywords=[],
            needs_review=True,
            reason=reason,
        )

    def _regulation_type(self, text: str) -> str | None:
        if any(token in text for token in ["arr_", "arr.", "arrete"]):
            return "arrete"
        if any(token in text for token in ["dec_", "dec.", "decret"]):
            return "decret"
        if any(token in text for token in ["loi", "law"]):
            return "loi"
        if any(token in text for token in ["circulaire", "note"]):
            return "circulaire"
        return None

    def _food_safety_keywords(self, text: str) -> list[str]:
        keywords = [
            "aliment",
            "agroalimentaire",
            "denree",
            "denrees",
            "denr",
            "sanitaire",
            "produits-alimentaires",
            "peche",
            "aquaculture",
            "codex",
            "hygiene",
            "agrement",
        ]
        return [keyword for keyword in keywords if keyword in text]
