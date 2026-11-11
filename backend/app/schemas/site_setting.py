from pydantic import BaseModel, Field


class SiteSettingsOut(BaseModel):
    site_name: str
    site_subtitle: str
    developer_name: str
    footer_text: str
    icp_no: str
    logo_url: str


class SiteSettingsUpdate(BaseModel):
    site_name: str | None = Field(default=None, max_length=40)
    site_subtitle: str | None = Field(default=None, max_length=80)
    icp_no: str | None = Field(default=None, max_length=60)
    logo_url: str | None = Field(default=None, max_length=500)
