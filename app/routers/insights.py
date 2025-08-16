from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
from app.models.schemas import BrandInsights, InsightRequest, CompetitorAnalysis
from app.services.shopify_scraper import ShopifyScraper
from app.services.groq_service import GroqService

router = APIRouter(prefix="/api/v1", tags=["insights"])

@router.post("/insights", response_model=BrandInsights)
async def get_brand_insights(request: InsightRequest):
    """
    Fetch brand insights from a Shopify store URL
    """
    try:
        logging.info(f"Processing insights request for: {request.website_url}")
        
        async with ShopifyScraper() as scraper:
            insights = await scraper.scrape_shopify_store(str(request.website_url))
            
            if insights.status == "error":
                logging.error(f"Scraper error: {insights.error_message}")
                if "not accessible" in insights.error_message.lower():
                    raise HTTPException(status_code=401, detail=insights.error_message)
                else:
                    raise HTTPException(status_code=500, detail=insights.error_message)
                    
            logging.info(f"Successfully extracted insights for {request.website_url}")
            return insights
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/competitor-analysis", response_model=CompetitorAnalysis)
async def get_competitor_analysis(request: InsightRequest):
    """
    BONUS: Get competitor analysis for a brand
    """
    try:
        async with ShopifyScraper() as scraper:
            groq_service = GroqService()
            
            # Get main brand insights
            main_insights = await scraper.scrape_shopify_store(str(request.website_url))
            
            if main_insights.status == "error":
                raise HTTPException(status_code=400, detail=main_insights.error_message)
            
            # Find competitors
            competitors_urls = await groq_service.find_competitors(
                main_insights.brand_name or "Unknown Brand"
            )
            
            # Get competitor insights
            competitor_insights = []
            for competitor_url in competitors_urls[:3]:  # Limit to 3 competitors
                if not competitor_url.startswith(('http://', 'https://')):
                    competitor_url = 'https://' + competitor_url
                    
                competitor_data = await scraper.scrape_shopify_store(competitor_url)
                if competitor_data.status == "success":
                    competitor_insights.append(competitor_data)
            
            return CompetitorAnalysis(
                main_brand=main_insights,
                competitors=competitor_insights
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in competitor analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to perform competitor analysis")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Shopify Insights API is running"}
