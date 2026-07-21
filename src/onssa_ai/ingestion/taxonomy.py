"""ONSSA site taxonomy mapping."""

from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml
from pydantic import BaseModel, Field


class TaxonomyRule(BaseModel):
    url_contains: str
    vertical: str
    domain: str
    subdomain: str
    sub_subdomain: str | None = None
    sub_subdomain_display: str | None = None
    display_path: list[str] = Field(default_factory=list)
    include_in_first_slice: bool = False


class TaxonomyConfig(BaseModel):
    default_vertical: str = "regulation"
    default_domain: str = "unclassified"
    default_subdomain: str = "unclassified"
    rules: list[TaxonomyRule] = Field(default_factory=list)


class TaxonomyMatch(BaseModel):
    matched: bool
    vertical: str
    domain: str
    subdomain: str
    display_path: list[str] = Field(default_factory=list)
    include_in_first_slice: bool = False
    matched_rule: str | None = None
    sub_subdomain: str | None = None
    sub_subdomain_display: str | None = None


class SiteTaxonomy:
    """Classify sources using ONSSA website URL hierarchy."""

    def __init__(self, config: TaxonomyConfig) -> None:
        self.config = config

    @classmethod
    def from_yaml(cls, path: Path) -> "SiteTaxonomy":
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        return cls(TaxonomyConfig.model_validate(data.get("taxonomy", {})))

    def match(self, source_url: str, parent_url: str | None) -> TaxonomyMatch:
        candidates = [parent_url or "", source_url]
        normalized_candidates = [self._normalize_url(candidate) for candidate in candidates]
        for rule in self.config.rules:
            normalized_rule = self._normalize_path(rule.url_contains)
            if any(normalized_rule in candidate for candidate in normalized_candidates):
                sub_subdomain_display = (
                    rule.sub_subdomain_display
                    or rule.sub_subdomain
                    or self._infer_sub_subdomain(source_url, rule)
                )
                return TaxonomyMatch(
                    matched=True,
                    vertical=rule.vertical,
                    domain=rule.domain,
                    subdomain=rule.subdomain,
                    display_path=rule.display_path,
                    include_in_first_slice=rule.include_in_first_slice,
                    matched_rule=rule.url_contains,
                    sub_subdomain=self._slugify(sub_subdomain_display),
                    sub_subdomain_display=sub_subdomain_display,
                )
        return TaxonomyMatch(
            matched=False,
            vertical=self.config.default_vertical,
            domain=self.config.default_domain,
            subdomain=self.config.default_subdomain,
        )

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(unquote(url))
        return self._normalize_path(parsed.path)

    def _normalize_path(self, path: str) -> str:
        normalized = unquote(path).lower()
        replacements = {
            "é": "e",
            "è": "e",
            "ê": "e",
            "à": "a",
            "ô": "o",
            "’": "",
            "'": "",
        }
        for source, target in replacements.items():
            normalized = normalized.replace(source, target)
        return normalized

    def _infer_sub_subdomain(self, source_url: str, rule: TaxonomyRule) -> str | None:
        path = unquote(urlparse(source_url).path)
        cleaned_parts = [self._clean_folder_name(part) for part in path.split("/") if part]
        for index, part in enumerate(cleaned_parts):
            if self._slugify(part) == rule.subdomain:
                for child in cleaned_parts[index + 1 :]:
                    if child and not child.lower().endswith(".pdf"):
                        return child
        return None

    def _clean_folder_name(self, value: str) -> str:
        value = value.replace("_", " ").strip()
        pieces = value.split(".", maxsplit=1)
        if len(pieces) == 2 and pieces[0].strip().isdigit():
            value = pieces[1].strip()
        return " ".join(value.split())

    def _slugify(self, value: str | None) -> str | None:
        if not value:
            return None
        normalized = self._normalize_path(value)
        chars = [char if char.isalnum() else "_" for char in normalized]
        slug = "_".join(part for part in "".join(chars).split("_") if part)
        return slug or None
