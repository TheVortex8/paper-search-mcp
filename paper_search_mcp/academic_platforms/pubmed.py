# paper_search_mcp/sources/pubmed.py
from typing import List
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
import logging
from ..paper import Paper
import os

# Configure logging
logger = logging.getLogger(__name__)

class PaperSource:
    """Abstract base class for paper sources"""
    def search(self, query: str, **kwargs) -> List[Paper]:
        raise NotImplementedError

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        raise NotImplementedError

    def read_paper(self, paper_id: str, save_path: str) -> str:
        raise NotImplementedError

class PubMedSearcher(PaperSource):
    """Searcher for PubMed papers"""
    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, api_key: str = None):
        """Initialize PubMed searcher with optional API key.
        
        Args:
            api_key: NCBI API key for higher rate limits and better performance
        """
        self.api_key = api_key

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        search_params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml'
        }
        
        # Add API key if available
        if self.api_key:
            search_params['api_key'] = self.api_key
            
        search_response = requests.get(self.SEARCH_URL, params=search_params)
        search_root = ET.fromstring(search_response.content)
        ids = [id.text for id in search_root.findall('.//Id')]
        
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(ids),
            'retmode': 'xml'
        }
        
        # Add API key if available
        if self.api_key:
            fetch_params['api_key'] = self.api_key
            
        fetch_response = requests.get(self.FETCH_URL, params=fetch_params)
        fetch_root = ET.fromstring(fetch_response.content)
        
        papers = []
        for article in fetch_root.findall('.//PubmedArticle'):
            try:
                pmid = article.find('.//PMID').text
                title = article.find('.//ArticleTitle').text
                authors = [f"{author.find('LastName').text} {author.find('Initials').text}" 
                           for author in article.findall('.//Author')]
                abstract = article.find('.//AbstractText').text if article.find('.//AbstractText') is not None else ''
                pub_date = article.find('.//PubDate/Year').text
                published = datetime.strptime(pub_date, '%Y')
                doi = article.find('.//ELocationID[@EIdType="doi"]').text if article.find('.//ELocationID[@EIdType="doi"]') is not None else ''
                papers.append(Paper(
                    paper_id=pmid,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    pdf_url='',  # PubMed 无直接 PDF
                    published_date=published,
                    updated_date=published,
                    source='pubmed',
                    categories=[],
                    keywords=[],
                    doi=doi
                ))
            except Exception as e:
                logger.error(f"Error parsing PubMed article: {e}")
        return papers

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        """Attempt to download a paper's PDF from PubMed.

        Args:
            paper_id: PubMed ID (PMID)
            save_path: Directory to save the PDF

        Returns:
            str: Error message indicating PDF download is not supported
        
        Raises:
            NotImplementedError: Always raises this error as PubMed doesn't provide direct PDF access
        """
        message = ("PubMed does not provide direct PDF downloads. "
                  "Please use the paper's DOI or URL to access the publisher's website.")
        raise NotImplementedError(message)

    def read_paper(self, paper_id: str, save_path: str = "./downloads") -> str:
        """Attempt to read and extract text from a PubMed paper.

        Args:
            paper_id: PubMed ID (PMID)
            save_path: Directory for potential PDF storage (unused)

        Returns:
            str: Error message indicating PDF reading is not supported
        """
        message = ("PubMed papers cannot be read directly through this tool. "
                  "Only metadata and abstracts are available through PubMed's API. "
                  "Please use the paper's DOI or URL to access the full text on the publisher's website.")
        return message

if __name__ == "__main__":
    # 测试 PubMedSearcher 的功能
    searcher = PubMedSearcher()
    
    # 测试搜索功能
    logger.info("Testing search functionality...")
    query = "machine learning"
    max_results = 5
    try:
        papers = searcher.search(query, max_results=max_results)
        logger.info(f"Found {len(papers)} papers for query '{query}':")
        for i, paper in enumerate(papers, 1):
            logger.info(f"{i}. {paper.title}")
            logger.info(f"   Authors: {', '.join(paper.authors)}")
            logger.info(f"   DOI: {paper.doi}")
            logger.info(f"   URL: {paper.url}\n")
    except Exception as e:
        logger.error(f"Error during search: {e}")
    
    # 测试 PDF 下载功能（会返回不支持的提示）
    if papers:
        logger.info("\nTesting PDF download functionality...")
        paper_id = papers[0].paper_id
        try:
            pdf_path = searcher.download_pdf(paper_id, "./downloads")
        except NotImplementedError as e:
            logger.warning(f"Expected error: {e}")
    
    # 测试论文阅读功能（会返回不支持的提示）
    if papers:
        logger.info("\nTesting paper reading functionality...")
        paper_id = papers[0].paper_id
        try:
            message = searcher.read_paper(paper_id)
            logger.info(f"Response: {message}")
        except Exception as e:
            logger.error(f"Error during paper reading: {e}")
