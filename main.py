#!/usr/bin/env python3
"""
Enhanced Lite BIWS: A Beautiful Web Scraping Library
"""

import requests
import json
import time
import logging
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from itertools import combinations
import random
from dataclasses import dataclass, asdict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lite_biws.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration class for scraping parameters."""
    base_keywords: List[str]
    query_char: str = "+"
    base_url: str = "https://www.google.com/search?q="
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 10
    user_agents: List[str] = None
    output_file: str = "LinksKeys-liteBiws.json"
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]


class LiteBiws:
    """Enhanced web scraping library for keyword-based URL extraction."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.session = requests.Session()
        self.scraped_urls: Set[str] = set()
        self.all_urls: List[List[str]] = []
        self.used_keywords: List[str] = []
        
    def generate_keyword_combinations(self) -> List[str]:
        """
        Generate all possible keyword combinations using itertools.
        More efficient than the original recursive approach.
        """
        combinations_list = []
        keywords = self.config.base_keywords
        
        # Generate combinations of different lengths (1 to n-1)
        for r in range(1, len(keywords)):
            for combo in combinations(keywords, r):
                keyword_string = self.config.query_char.join(combo)
                combinations_list.append(keyword_string)
        
        logger.info(f"Generated {len(combinations_list)} keyword combinations")
        return combinations_list
    
    def get_random_user_agent(self) -> str:
        """Return a random user agent to avoid detection."""
        return random.choice(self.config.user_agents)
    
    def make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """
        Make HTTP request with error handling and retries.
        """
        if retries >= self.config.max_retries:
            logger.error(f"Max retries exceeded for URL: {url}")
            return None
        
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            # Add delay to avoid rate limiting
            time.sleep(self.config.request_delay)
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            time.sleep(2 ** retries)  # Exponential backoff
            return self.make_request(url, retries + 1)
    
    def extract_google_urls(self, html_content: str) -> List[str]:
        """
        Extract URLs from Google search results with improved parsing.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        urls = []
        
        # Multiple selectors for different Google result formats
        selectors = [
            'a[href^="/url?q="]',
            'a[href^="http"]',
            '.yuRUbf a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                
                if href.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    actual_url = href[7:]  # Remove '/url?q='
                    if '&sa=' in actual_url:
                        actual_url = actual_url[:actual_url.find('&sa=')]
                    urls.append(actual_url)
                elif href.startswith('http') and 'google.com' not in href:
                    urls.append(href)
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            if url not in seen and self.is_valid_url(url):
                unique_urls.append(url)
                seen.add(url)
        
        return unique_urls
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a Google internal link."""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                'google.com' not in parsed.netloc.lower() and
                'googleusercontent.com' not in parsed.netloc.lower()
            )
        except Exception:
            return False
    
    def extract_meta_keywords(self, html_content: str) -> List[str]:
        """
        Extract meta keywords from HTML content with improved parsing.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        keywords = []
        
        # Multiple approaches to find keywords
        selectors = [
            'meta[name="keywords"]',
            'meta[name="Keywords"]',
            'meta[property="keywords"]',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            meta_tags = soup.select(selector)
            for tag in meta_tags:
                content = tag.get('content', '').strip()
                if content:
                    # Split by common delimiters
                    for delimiter in [',', ';', '|']:
                        if delimiter in content:
                            keywords.extend([kw.strip() for kw in content.split(delimiter)])
                            break
                    else:
                        keywords.append(content)
        
        return [kw for kw in keywords if kw and len(kw.strip()) > 0]
    
    def scrape_search_results(self) -> None:
        """
        Main method to scrape search results for all keyword combinations.
        """
        search_keywords = self.generate_keyword_combinations()
        
        logger.info(f"Starting scraping for {len(search_keywords)} keyword combinations")
        
        for i, keywords in enumerate(search_keywords, 1):
            logger.info(f"Processing keyword combination {i}/{len(search_keywords)}: {keywords}")
            
            search_url = f"{self.config.base_url}{keywords}"
            response = self.make_request(search_url)
            
            if not response:
                logger.warning(f"Failed to fetch search results for: {keywords}")
                continue
            
            urls = self.extract_google_urls(response.text)
            self.all_urls.append(urls)
            
            logger.info(f"Found {len(urls)} URLs for keywords: {keywords}")
            
            # Extract meta keywords from each URL
            self.extract_keywords_from_urls(urls)
    
    def extract_keywords_from_urls(self, urls: List[str]) -> None:
        """
        Extract meta keywords from a list of URLs.
        """
        for url in urls:
            if url in self.scraped_urls:
                continue
                
            self.scraped_urls.add(url)
            logger.info(f"Extracting keywords from: {url}")
            
            response = self.make_request(url)
            if not response:
                continue
            
            try:
                keywords = self.extract_meta_keywords(response.text)
                self.used_keywords.extend(keywords)
                logger.info(f"Extracted {len(keywords)} keywords from {url}")
                
            except Exception as e:
                logger.error(f"Error extracting keywords from {url}: {e}")
    
    def get_statistics(self) -> Dict:
        """Get scraping statistics."""
        return {
            'total_search_queries': len(self.all_urls),
            'total_urls_found': sum(len(urls) for urls in self.all_urls),
            'unique_urls_scraped': len(self.scraped_urls),
            'total_keywords_extracted': len(self.used_keywords),
            'unique_keywords': len(set(self.used_keywords))
        }
    
    def export_results(self) -> None:
        """
        Export results to JSON file with enhanced structure.
        """
        # Remove duplicates from keywords while preserving order
        unique_keywords = []
        seen_keywords = set()
        for keyword in self.used_keywords:
            if keyword.lower() not in seen_keywords:
                unique_keywords.append(keyword)
                seen_keywords.add(keyword.lower())
        
        results = {
            'metadata': {
                'scraping_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'base_keywords': self.config.base_keywords,
                'statistics': self.get_statistics()
            },
            'search_results': {
                'urls_by_query': self.all_urls,
                'all_unique_urls': list(self.scraped_urls)
            },
            'extracted_data': {
                'keywords': unique_keywords,
                'keyword_count': len(unique_keywords)
            }
        }
        
        try:
            with open(self.config.output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results exported to {self.config.output_file}")
            logger.info(f"Scraping statistics: {self.get_statistics()}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
    
    def run(self) -> None:
        """
        Main execution method.
        """
        try:
            logger.info("Starting lite-Biws web scraping...")
            self.scrape_search_results()
            self.export_results()
            logger.info("Scraping completed successfully!")
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            self.export_results()  # Save partial results
            
        except Exception as e:
            logger.error(f"Fatal error during scraping: {e}")
            raise


def main():
    """Main function to run the scraper."""
    
    # Configuration
    config = ScrapingConfig(
        base_keywords=["daa", "system", "simple", "functional"],
        query_char="+",
        request_delay=1.5,  # Increased delay to be more respectful
        max_retries=3,
        timeout=15,
        output_file="LinksKeys-liteBiws-enhanced.json"
    )
    
    # Initialize and run scraper
    scraper = LiteBiws(config)
    scraper.run()


if __name__ == "__main__":
    main()
