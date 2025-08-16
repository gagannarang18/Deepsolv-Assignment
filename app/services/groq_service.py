import os
from groq import Groq
from typing import Dict, List, Any, Optional
import json
import logging

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-70b-versatile"
        
    async def extract_brand_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract brand information from HTML content using Groq"""
        try:
            prompt = f"""
            Analyze the following HTML content from {url} and extract brand information.
            Return a JSON object with the following structure:
            {{
                "brand_name": "extracted brand name",
                "brand_description": "about the brand text",
                "contact_emails": ["email1", "email2"],
                "contact_phones": ["phone1", "phone2"],
                "social_handles": {{
                    "instagram": "instagram_handle",
                    "facebook": "facebook_url",
                    "twitter": "twitter_handle",
                    "tiktok": "tiktok_handle",
                    "youtube": "youtube_url",
                    "linkedin": "linkedin_url"
                }}
            }}

            HTML Content (first 8000 chars):
            {html_content[:8000]}
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert at extracting brand information from websites. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON from Groq response")
            return {}
        except Exception as e:
            logging.error(f"Groq API error: {str(e)}")
            return {}

    async def extract_faqs(self, html_content: str) -> List[Dict[str, str]]:
        """Extract FAQs from HTML content"""
        try:
            prompt = f"""
            Extract all FAQ questions and answers from the following HTML content.
            Return a JSON array with this structure:
            [
                {{"question": "Do you have COD?", "answer": "Yes, we offer Cash on Delivery"}},
                {{"question": "What is your return policy?", "answer": "30 days return policy"}}
            ]

            HTML Content (first 6000 chars):
            {html_content[:6000]}
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Extract FAQ information and return as JSON array. If no FAQs found, return empty array."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=1500
            )
            
            result = response.choices.message.content
            return json.loads(result)
            
        except:
            return []

    async def find_competitors(self, brand_name: str, industry: str = "") -> List[str]:
        """Find competitor websites for a brand"""
        try:
            prompt = f"""
            Given the brand name "{brand_name}" {f"in {industry} industry" if industry else ""}, 
            suggest 3-5 main competitor websites. Return only the website URLs in JSON format:
            ["competitor1.com", "competitor2.com", "competitor3.com"]
            
            Focus on direct competitors that are likely to have Shopify stores.
            """
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a market research expert. Return only competitor website URLs in JSON array format."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except:
            return []
