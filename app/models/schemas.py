from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class ProductSchema(BaseModel):
    id: Optional[str] = None
    title: str
    handle: str
    price: Optional[str] = None
    compare_at_price: Optional[str] = None
    available: bool
    images: List[str] = []
    variants: List[Dict[str, Any]] = []
    tags: List[str] = []
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    description: Optional[str] = None

class ContactInfo(BaseModel):
    emails: List[str] = []
    phones: List[str] = []
    addresses: List[str] = []

class SocialHandles(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    tiktok: Optional[str] = None
    youtube: Optional[str] = None
    linkedin: Optional[str] = None

class FAQ(BaseModel):
    question: str
    answer: str

class PolicyInfo(BaseModel):
    privacy_policy: Optional[str] = None
    return_policy: Optional[str] = None
    refund_policy: Optional[str] = None
    terms_of_service: Optional[str] = None
    shipping_policy: Optional[str] = None

class BrandInsights(BaseModel):
    website_url: str
    brand_name: Optional[str] = None
    brand_description: Optional[str] = None
    product_catalog: List[ProductSchema] = []
    hero_products: List[ProductSchema] = []
    contact_info: ContactInfo = ContactInfo()
    social_handles: SocialHandles = SocialHandles()
    policies: PolicyInfo = PolicyInfo()
    faqs: List[FAQ] = []
    important_links: Dict[str, str] = {}
    total_products: int = 0
    scraped_at: datetime = datetime.now()
    status: str = "success"
    error_message: Optional[str] = None

class InsightRequest(BaseModel):
    website_url: HttpUrl

class CompetitorAnalysis(BaseModel):
    main_brand: BrandInsights
    competitors: List[BrandInsights] = []
