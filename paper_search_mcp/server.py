# paper_search_mcp/server.py
from typing import List, Dict, Optional
import httpx
import os
import logging
import asyncio
import time
from mcp.server.fastmcp import FastMCP
from .academic_platforms.arxiv import ArxivSearcher
from .academic_platforms.pubmed import PubMedSearcher
from .academic_platforms.biorxiv import BioRxivSearcher
from .academic_platforms.medrxiv import MedRxivSearcher
from .academic_platforms.google_scholar import GoogleScholarSearcher
from .academic_platforms.iacr import IACRSearcher
from .academic_platforms.semantic import SemanticSearcher
from .academic_platforms.crossref import CrossRefSearcher

# from .academic_platforms.hub import SciHubSearcher
from .paper import Paper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("paper_search_server")

# Read NCBI API key from environment
ncbi_api_key = os.getenv("NCBI_API_KEY")

# Global initialization flag
_initialized = False
_initialization_lock = asyncio.Lock()

# Instances of searchers (will be initialized later)
arxiv_searcher = None
pubmed_searcher = None
biorxiv_searcher = None
medrxiv_searcher = None
google_scholar_searcher = None
iacr_searcher = None
semantic_searcher = None
crossref_searcher = None
# scihub_searcher = None

async def ensure_initialized():
    """Ensure all searchers are initialized before handling requests."""
    global _initialized, arxiv_searcher, pubmed_searcher, biorxiv_searcher
    global medrxiv_searcher, google_scholar_searcher, iacr_searcher
    global semantic_searcher, crossref_searcher
    
    if _initialized:
        return
        
    async with _initialization_lock:
        if _initialized:  # Double-check pattern
            return
            
        logger.info("Initializing searchers...")
        try:
            # Initialize searchers in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def init_searchers():
                try:
                    logger.info("Creating searcher instances...")
                    return {
                        'arxiv': ArxivSearcher(),
                        'pubmed': PubMedSearcher(api_key=ncbi_api_key),
                        'biorxiv': BioRxivSearcher(),
                        'medrxiv': MedRxivSearcher(),
                        'google_scholar': GoogleScholarSearcher(),
                        'iacr': IACRSearcher(),
                        'semantic': SemanticSearcher(),
                        'crossref': CrossRefSearcher(),
                    }
                except Exception as e:
                    logger.error(f"Error creating searcher instances: {e}")
                    raise
            
            # Add timeout to prevent hanging
            searchers = await asyncio.wait_for(
                loop.run_in_executor(None, init_searchers),
                timeout=30.0  # 30 second timeout
            )
            
            arxiv_searcher = searchers['arxiv']
            pubmed_searcher = searchers['pubmed']
            biorxiv_searcher = searchers['biorxiv']
            medrxiv_searcher = searchers['medrxiv']
            google_scholar_searcher = searchers['google_scholar']
            iacr_searcher = searchers['iacr']
            semantic_searcher = searchers['semantic']
            crossref_searcher = searchers['crossref']
            
            _initialized = True
            logger.info("All searchers initialized successfully")
            
        except asyncio.TimeoutError:
            logger.error("Timeout during searcher initialization")
            raise RuntimeError("Initialization timeout - searchers took too long to initialize")
        except Exception as e:
            logger.error(f"Failed to initialize searchers: {e}")
            # Reset initialization flag so we can retry
            _initialized = False
            raise


# Asynchronous helper to adapt synchronous searchers
async def async_search(searcher, query: str, max_results: int, **kwargs) -> List[Dict]:
    # Ensure initialization before processing
    await ensure_initialized()
    
    if searcher is None:
        logger.error("Searcher is None - initialization may have failed")
        return []
    
    # Run synchronous searcher calls in a thread pool to avoid blocking
    def sync_search():
        if 'year' in kwargs:
            return searcher.search(query, year=kwargs['year'], max_results=max_results)
        else:
            return searcher.search(query, max_results=max_results)
    
    try:
        papers = await asyncio.get_event_loop().run_in_executor(None, sync_search)
        return [paper.to_dict() for paper in papers] if papers else []
    except Exception as e:
        logger.error(f"Error in async_search with {searcher.__class__.__name__}: {e}")
        return []


# Tool definitions
@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from arXiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    papers = await async_search(arxiv_searcher, query, max_results)
    return papers if papers else []


@mcp.tool()
async def search_pubmed(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from PubMed.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    papers = await async_search(pubmed_searcher, query, max_results)
    return papers if papers else []


@mcp.tool()
async def search_biorxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from bioRxiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    papers = await async_search(biorxiv_searcher, query, max_results)
    return papers if papers else []


@mcp.tool()
async def search_medrxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from medRxiv.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    papers = await async_search(medrxiv_searcher, query, max_results)
    return papers if papers else []


@mcp.tool()
async def search_google_scholar(query: str, max_results: int = 10) -> List[Dict]:
    """Search academic papers from Google Scholar.

    Args:
        query: Search query string (e.g., 'machine learning').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    papers = await async_search(google_scholar_searcher, query, max_results)
    return papers if papers else []


@mcp.tool()
async def search_iacr(
    query: str, max_results: int = 10, fetch_details: bool = True
) -> List[Dict]:
    """Search academic papers from IACR ePrint Archive.

    Args:
        query: Search query string (e.g., 'cryptography', 'secret sharing').
        max_results: Maximum number of papers to return (default: 10).
        fetch_details: Whether to fetch detailed information for each paper (default: True).
    Returns:
        List of paper metadata in dictionary format.
    """
    await ensure_initialized()
    
    if iacr_searcher is None:
        logger.error("IACR searcher not initialized")
        return []
        
    try:
        papers = await asyncio.get_event_loop().run_in_executor(
            None, lambda: iacr_searcher.search(query, max_results, fetch_details)
        )
        return [paper.to_dict() for paper in papers] if papers else []
    except Exception as e:
        logger.error(f"Error in search_iacr: {e}")
        return []


@mcp.tool()
async def download_arxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of an arXiv paper.

    Args:
        paper_id: arXiv paper ID (e.g., '2106.12345').
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        Path to the downloaded PDF file.
    """
    await ensure_initialized()
    
    if arxiv_searcher is None:
        logger.error("ArXiv searcher not initialized")
        return "Error: ArXiv searcher not initialized"
        
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: arxiv_searcher.download_pdf(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error downloading arxiv paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def download_pubmed(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to download PDF of a PubMed paper.

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        str: Message indicating that direct PDF download is not supported.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: pubmed_searcher.download_pdf(paper_id, save_path)
        )
    except NotImplementedError as e:
        return str(e)
    except Exception as e:
        logger.error(f"Error in download_pubmed: {e}")
        return f"Error: {e}"


@mcp.tool()
async def download_biorxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a bioRxiv paper.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        Path to the downloaded PDF file.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: biorxiv_searcher.download_pdf(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error downloading biorxiv paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def download_medrxiv(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a medRxiv paper.

    Args:
        paper_id: medRxiv DOI.
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        Path to the downloaded PDF file.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: medrxiv_searcher.download_pdf(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error downloading medrxiv paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def download_iacr(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of an IACR ePrint paper.

    Args:
        paper_id: IACR paper ID (e.g., '2009/101').
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        Path to the downloaded PDF file.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: iacr_searcher.download_pdf(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error downloading iacr paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def read_arxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from an arXiv paper PDF.

    Args:
        paper_id: arXiv paper ID (e.g., '2106.12345').
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: The extracted text content of the paper.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: arxiv_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_pubmed_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a PubMed paper.

    Args:
        paper_id: PubMed ID (PMID).
        save_path: Directory where the PDF would be saved (unused).
    Returns:
        str: Message indicating that direct paper reading is not supported.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: pubmed_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading pubmed paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def read_biorxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a bioRxiv paper PDF.

    Args:
        paper_id: bioRxiv DOI.
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: The extracted text content of the paper.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: biorxiv_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_medrxiv_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a medRxiv paper PDF.

    Args:
        paper_id: medRxiv DOI.
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: The extracted text content of the paper.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: medrxiv_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def read_iacr_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from an IACR ePrint paper PDF.

    Args:
        paper_id: IACR paper ID (e.g., '2009/101').
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: The extracted text content of the paper.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: iacr_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def search_semantic(query: str, year: Optional[str] = None, max_results: int = 10) -> List[Dict]:
    """Search academic papers from Semantic Scholar.

    Args:
        query: Search query string (e.g., 'machine learning').
        year: Optional year filter (e.g., '2019', '2016-2020', '2010-', '-2015').
        max_results: Maximum number of papers to return (default: 10).
    Returns:
        List of paper metadata in dictionary format.
    """
    kwargs = {}
    if year is not None:
        kwargs['year'] = year
    papers = await async_search(semantic_searcher, query, max_results, **kwargs)
    return papers if papers else []


@mcp.tool()
async def download_semantic(paper_id: str, save_path: str = "./downloads") -> str:
    """Download PDF of a Semantic Scholar paper.    

    Args:
        paper_id: Semantic Scholar paper ID, Paper identifier in one of the following formats:
            - Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b")
            - DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011")
            - ARXIV:<id> (e.g., "ARXIV:2106.15928")
            - MAG:<id> (e.g., "MAG:112218234")
            - ACL:<id> (e.g., "ACL:W12-3903")
            - PMID:<id> (e.g., "PMID:19872477")
            - PMCID:<id> (e.g., "PMCID:2323736")
            - URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        Path to the downloaded PDF file.
    """ 
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: semantic_searcher.download_pdf(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error downloading semantic paper {paper_id}: {e}")
        return f"Error: {e}"


@mcp.tool()
async def read_semantic_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Read and extract text content from a Semantic Scholar paper. 

    Args:
        paper_id: Semantic Scholar paper ID, Paper identifier in one of the following formats:
            - Semantic Scholar ID (e.g., "649def34f8be52c8b66281af98ae884c09aef38b")
            - DOI:<doi> (e.g., "DOI:10.18653/v1/N18-3011")
            - ARXIV:<id> (e.g., "ARXIV:2106.15928")
            - MAG:<id> (e.g., "MAG:112218234")
            - ACL:<id> (e.g., "ACL:W12-3903")
            - PMID:<id> (e.g., "PMID:19872477")
            - PMCID:<id> (e.g., "PMCID:2323736")
            - URL:<url> (e.g., "URL:https://arxiv.org/abs/2106.15928v1")
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: The extracted text content of the paper.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: semantic_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading paper {paper_id}: {e}")
        return ""


@mcp.tool()
async def search_crossref(query: str, max_results: int = 10, **kwargs) -> List[Dict]:
    """Search academic papers from CrossRef database.
    
    CrossRef is a scholarly infrastructure organization that provides 
    persistent identifiers (DOIs) for scholarly content and metadata.
    It's one of the largest citation databases covering millions of 
    academic papers, journals, books, and other scholarly content.

    Args:
        query: Search query string (e.g., 'machine learning', 'climate change').
        max_results: Maximum number of papers to return (default: 10, max: 1000).
        **kwargs: Additional search parameters:
            - filter: CrossRef filter string (e.g., 'has-full-text:true,from-pub-date:2020')
            - sort: Sort field ('relevance', 'published', 'updated', 'deposited', etc.)
            - order: Sort order ('asc' or 'desc')
    Returns:
        List of paper metadata in dictionary format.
        
    Examples:
        # Basic search
        search_crossref("deep learning", 20)
        
        # Search with filters
        search_crossref("climate change", 10, filter="from-pub-date:2020,has-full-text:true")
        
        # Search sorted by publication date
        search_crossref("neural networks", 15, sort="published", order="desc")
    """
    papers = await async_search(crossref_searcher, query, max_results, **kwargs)
    return papers if papers else []


@mcp.tool()
async def get_crossref_paper_by_doi(doi: str) -> Dict:
    """Get a specific paper from CrossRef by its DOI.

    Args:
        doi: Digital Object Identifier (e.g., '10.1038/nature12373').
    Returns:
        Paper metadata in dictionary format, or empty dict if not found.
        
    Example:
        get_crossref_paper_by_doi("10.1038/nature12373")
    """
    await ensure_initialized()
    
    if crossref_searcher is None:
        logger.error("CrossRef searcher not initialized")
        return {}
        
    try:
        paper = await asyncio.get_event_loop().run_in_executor(
            None, lambda: crossref_searcher.get_paper_by_doi(doi)
        )
        return paper.to_dict() if paper else {}
    except Exception as e:
        logger.error(f"Error getting crossref paper by DOI {doi}: {e}")
        return {}


@mcp.tool()
async def download_crossref(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to download PDF of a CrossRef paper.

    Args:
        paper_id: CrossRef DOI (e.g., '10.1038/nature12373').
        save_path: Directory to save the PDF (default: './downloads').
    Returns:
        str: Message indicating that direct PDF download is not supported.
        
    Note:
        CrossRef is a citation database and doesn't provide direct PDF downloads.
        Use the DOI to access the paper through the publisher's website.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: crossref_searcher.download_pdf(paper_id, save_path)
        )
    except NotImplementedError as e:
        return str(e)
    except Exception as e:
        logger.error(f"Error in download_crossref: {e}")
        return f"Error: {e}"


@mcp.tool()
async def read_crossref_paper(paper_id: str, save_path: str = "./downloads") -> str:
    """Attempt to read and extract text content from a CrossRef paper.

    Args:
        paper_id: CrossRef DOI (e.g., '10.1038/nature12373').
        save_path: Directory where the PDF is/will be saved (default: './downloads').
    Returns:
        str: Message indicating that direct paper reading is not supported.
        
    Note:
        CrossRef is a citation database and doesn't provide direct paper content.
        Use the DOI to access the paper through the publisher's website.
    """
    import asyncio
    try:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: crossref_searcher.read_paper(paper_id, save_path)
        )
    except Exception as e:
        logger.error(f"Error reading crossref paper {paper_id}: {e}")
        return f"Error: {e}"


async def startup_handler():
    """Handle server startup initialization."""
    logger.info("Starting server initialization...")
    
    # Log NCBI API key status
    if ncbi_api_key:
        logger.info(f"NCBI API key detected (length: {len(ncbi_api_key)} chars)")
    else:
        logger.warning("No NCBI API key found - using rate-limited public access")
    
    # Pre-initialize all searchers with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await ensure_initialized()
            logger.info("Server initialization complete")
            return
        except Exception as e:
            logger.error(f"Initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying initialization in 2 seconds...")
                await asyncio.sleep(2)
            else:
                logger.error("All initialization attempts failed")
                raise

@mcp.tool()
async def health_check() -> Dict:
    """Check the health status of the paper search server.
    
    Returns:
        Dictionary containing health status and initialization state.
    """
    global _initialized
    return {
        "status": "healthy" if _initialized else "initializing",
        "initialized": _initialized,
        "searchers_available": {
            "arxiv": arxiv_searcher is not None,
            "pubmed": pubmed_searcher is not None,
            "biorxiv": biorxiv_searcher is not None,
            "medrxiv": medrxiv_searcher is not None,
            "google_scholar": google_scholar_searcher is not None,
            "iacr": iacr_searcher is not None,
            "semantic": semantic_searcher is not None,
            "crossref": crossref_searcher is not None,
        },
        "ncbi_api_key_configured": ncbi_api_key is not None,
        "timestamp": time.time()
    }

# Startup will be handled by ensure_initialized() calls

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Search MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run as stdio server instead of HTTP server")
    
    args = parser.parse_args()
    
    # Log NCBI API key status on startup
    if ncbi_api_key:
        logger.info(f"NCBI API key detected (length: {len(ncbi_api_key)} chars)")
    else:
        logger.warning("No NCBI API key found - using rate-limited public access")
    
    if args.stdio:
        # Run as stdio server
        logger.info("Starting MCP Paper Search Server in stdio mode")
        mcp.run(transport="stdio")
    else:
        # Run as HTTP server (default)
        logger.info("Starting MCP Paper Search Server in HTTP mode")
        mcp.run(transport="sse")
