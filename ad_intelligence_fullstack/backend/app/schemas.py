from typing import Any
from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    company: str = Field(min_length=1, max_length=100)
    competitor: str = Field(min_length=1, max_length=100)

    @field_validator("company", "competitor")
    @classmethod
    def strip_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Brand names cannot be empty")
        return value


class AdRecord(BaseModel):
    advertiser_name: str
    ad_archive_id: str | None = None
    ad_text: str = ""
    headline: str = ""
    start_date: str | None = None
    platforms: list[str] = Field(default_factory=list)
    media_type: str | None = None
    landing_page_url: str | None = None
    ad_library_url: str | None = None
    image_url: str | None = None
    source_verified: bool = False
    creative_analysis: dict[str, Any] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    company: str
    competitor: str
    demo_mode: bool
    collection_status: str
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, Any]
    comparison: dict[str, Any]
    opportunities: list[dict[str, Any]]
    ads: dict[str, list[AdRecord]]
    clusters: dict[str, Any] = Field(default_factory=dict)
