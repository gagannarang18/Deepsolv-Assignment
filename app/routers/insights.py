from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
import asyncio
from app.models.schemas import BrandInsights, InsightRequest, CompetitorAnalysis
from app.services.shopify_scraper import ShopifyScraper
from app.services.groq_service import GroqService

router = APIRouter(prefix="/api/v1", tags=["insights"])

@router.post("/insights", response_model=BrandInsights)
async def get_brand_insights(request: InsightRequest):
    try:
        # URL normalization
        url = str(request.website_url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        logging.info(f"Processing insights request for: {url}")
        
        async with ShopifyScraper() as scraper:
            insights = await scraper.scrape_shopify_store(url)
            
            if insights.status == "error":
                if "not accessible" in insights.error_message.lower():
                    raise HTTPException(
                        status_code=401, 
                        detail=f"Website '{url}' is not accessible. Please check the URL or try a different Shopify store."
                    )
                else:
                    raise HTTPException(status_code=500, detail=insights.error_message)
            
            return insights
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error occurred")


@router.post("/competitor-analysis", response_model=CompetitorAnalysis)
async def get_competitor_analysis(request: InsightRequest):
    try:
        # URL normalization
        url = str(request.website_url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        async with ShopifyScraper() as scraper:
            groq_service = GroqService()
            
            # Get main brand insights
            main_insights = await scraper.scrape_shopify_store(url)
            
            if main_insights.status == "error":
                if "not accessible" in main_insights.error_message.lower():
                    raise HTTPException(
                        status_code=401, 
                        detail=f"Website '{url}' is not accessible. Please check the URL."
                    )
                else:
                    raise HTTPException(status_code=400, detail=main_insights.error_message)
            
            # Find competitors with concurrent fetching
            competitors_urls = await groq_service.find_competitors(
                main_insights.brand_name or "Unknown Brand"
            )
            
            async def fetch_competitor(comp_url):
                if not comp_url.startswith(('http://', 'https://')):
                    comp_url = 'https://' + comp_url
                try:
                    # Add delay between competitor requests
                    await asyncio.sleep(1)
                    competitor_data = await scraper.scrape_shopify_store(comp_url)
                    return competitor_data if competitor_data.status == "success" else None
                except Exception as ex:
                    logging.error(f"Failed to fetch competitor {comp_url}: {ex}")
                    return None

            competitor_tasks = [fetch_competitor(url) for url in competitors_urls[:2]]  # Limit to 2
            competitor_results = await asyncio.gather(*competitor_tasks)
            competitor_insights = [c for c in competitor_results if c is not None]

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
