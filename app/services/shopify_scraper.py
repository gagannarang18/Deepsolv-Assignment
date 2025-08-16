import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import re
import logging
from app.models.schemas import ProductSchema, BrandInsights, ContactInfo, SocialHandles, PolicyInfo, FAQ
from app.services.groq_service import GroqService

class ShopifyScraper:
    def __init__(self):
        self.groq_service = GroqService()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_url(self, url: str) -> Tuple[str, int]:
        """Fetch URL content and return HTML and status code"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return html, response.status
                return "", response.status
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return "", 500

    async def get_products_json(self, base_url: str) -> List[Dict[str, Any]]:
        """Fetch products from /products.json endpoint"""
        products = []
        page = 1
        
        while True:
            url = f"{base_url.rstrip('/')}/products.json?limit=250&page={page}"
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_products = data.get('products', [])
                        if not page_products:
                            break
                        products.extend(page_products)
                        page += 1
                        if len(page_products) < 250:  # Last page
                            break
                    else:
                        break
            except Exception as e:
                logging.error(f"Error fetching products page {page}: {str(e)}")
                break
                
        return products

    def parse_product(self, product_data: Dict[str, Any]) -> ProductSchema:
        """Parse product data into ProductSchema"""
        try:
            images = []
            if 'images' in product_data:
                images = [img.get('src', '') for img in product_data['images']]
            
            variants = product_data.get('variants', [])
            price = None
            if variants:
                price = str(variants[0].get('price', '0'))
            
            tags = []
            if 'tags' in product_data:
                if isinstance(product_data['tags'], str):
                    tags = [tag.strip() for tag in product_data['tags'].split(',')]
                else:
                    tags = product_data['tags']
            
            return ProductSchema(
                id=str(product_data.get('id', '')),
                title=product_data.get('title', ''),
                handle=product_data.get('handle', ''),
                price=price,
                available=any(variant.get('available', False) for variant in variants),
                images=images,
                variants=variants,
                tags=tags,
                vendor=product_data.get('vendor', ''),
                product_type=product_data.get('product_type', ''),
                description=product_data.get('body_html', '')
            )
        except Exception as e:
            logging.error(f"Error parsing product: {str(e)}")
            return ProductSchema(title="Parse Error", handle="error")

    async def extract_hero_products(self, html: str, all_products: List[ProductSchema]) -> List[ProductSchema]:
        """Extract hero products from homepage"""
        soup = BeautifulSoup(html, 'html.parser')
        hero_products = []
        
        # Look for product links on homepage
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        product_handles = set()
        
        for link in product_links[:10]:  # Limit to first 10 found
            href = link.get('href', '')
            if '/products/' in href:
                handle = href.split('/products/')[-1].split('?')[0].split('#')
                product_handles.add(handle)
        
        # Match with actual products
        for product in all_products:
            if product.handle in product_handles:
                hero_products.append(product)
                if len(hero_products) >= 8:  # Reasonable limit
                    break
                    
        return hero_products

    async def extract_policies(self, base_url: str) -> PolicyInfo:
        """Extract policy information"""
        policies = PolicyInfo()
        policy_urls = {
            'privacy_policy': ['/pages/privacy-policy', '/policies/privacy-policy', '/privacy'],
            'return_policy': ['/pages/return-policy', '/policies/refund-policy', '/returns'],
            'refund_policy': ['/pages/refund-policy', '/policies/refund-policy', '/refunds'],
            'terms_of_service': ['/pages/terms-of-service', '/policies/terms-of-service', '/terms'],
            'shipping_policy': ['/pages/shipping-policy', '/policies/shipping-policy', '/shipping']
        }
        
        for policy_type, urls in policy_urls.items():
            for url_path in urls:
                full_url = urljoin(base_url, url_path)
                html, status = await self.fetch_url(full_url)
                if status == 200 and html:
                    setattr(policies, policy_type, full_url)
                    break  # Found policy, move to next type
                    
        return policies

    def extract_important_links(self, html: str, base_url: str) -> Dict[str, str]:
        """Extract important links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        important_links = {}
        
        # Common important link patterns
        link_patterns = {
            'Contact Us': ['/pages/contact', '/contact', '/contact-us'],
            'About Us': ['/pages/about', '/about', '/about-us'],
            'Order Tracking': ['/account/login', '/track', '/tracking'],
            'Blog': ['/blogs', '/blog'],
            'Support': ['/pages/support', '/support', '/help'],
            'Size Guide': ['/pages/size-guide', '/size-guide'],
            'FAQ': ['/pages/faq', '/faq', '/pages/frequently-asked-questions']
        }
        
        # Find links in navigation and footer
        for link_name, patterns in link_patterns.items():
            for pattern in patterns:
                link_elem = soup.find('a', href=re.compile(pattern, re.IGNORECASE))
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        important_links[link_name] = full_url
                        break
                        
        return important_links

    async def scrape_shopify_store(self, url: str) -> BrandInsights:
        """Main method to scrape Shopify store"""
        try:
            # Validate and normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Fetch homepage
            html, status = await self.fetch_url(url)
            if status != 200:
                return BrandInsights(
                    website_url=url,
                    status="error",
                    error_message=f"Website not accessible. Status code: {status}"
                )

            # Check if it's likely a Shopify store
            if 'shopify' not in html.lower() and 'cdn.shopify.com' not in html:
                # Try to fetch products.json to confirm
                products_data = await self.get_products_json(url)
                if not products_data:
                    return BrandInsights(
                        website_url=url,
                        status="error",
                        error_message="Not a Shopify store or products not accessible"
                    )

            # Get all products
            products_data = await self.get_products_json(url)
            all_products = [self.parse_product(product) for product in products_data]
            
            # Extract hero products
            hero_products = await self.extract_hero_products(html, all_products)
            
            # Extract brand info using Groq
            brand_info = await self.groq_service.extract_brand_info(html, url)
            
            # Extract FAQs
            faq_html, _ = await self.fetch_url(urljoin(url, '/pages/faq'))
            if not faq_html:
                faq_html = html  # Use homepage if no FAQ page
            faqs_data = await self.groq_service.extract_faqs(faq_html)
            faqs = [FAQ(question=faq.get('question', ''), answer=faq.get('answer', '')) 
                   for faq in faqs_data if faq.get('question') and faq.get('answer')]
            
            # Extract policies
            policies = await self.extract_policies(url)
            
            # Extract important links
            important_links = self.extract_important_links(html, url)
            
            # Build contact info
            contact_info = ContactInfo(
                emails=brand_info.get('contact_emails', []),
                phones=brand_info.get('contact_phones', [])
            )
            
            # Build social handles
            social_data = brand_info.get('social_handles', {})
            social_handles = SocialHandles(
                instagram=social_data.get('instagram'),
                facebook=social_data.get('facebook'),
                twitter=social_data.get('twitter'),
                tiktok=social_data.get('tiktok'),
                youtube=social_data.get('youtube'),
                linkedin=social_data.get('linkedin')
            )
            
            return BrandInsights(
                website_url=url,
                brand_name=brand_info.get('brand_name', ''),
                brand_description=brand_info.get('brand_description', ''),
                product_catalog=all_products,
                hero_products=hero_products,
                contact_info=contact_info,
                social_handles=social_handles,
                policies=policies,
                faqs=faqs,
                important_links=important_links,
                total_products=len(all_products),
                status="success"
            )
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return BrandInsights(
                website_url=url,
                status="error",
                error_message=str(e)
            )
