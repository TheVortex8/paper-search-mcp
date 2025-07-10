# Paper Search MCP

A Model Context Protocol (MCP) server for searching and downloading academic papers from multiple sources, including arXiv, PubMed, bioRxiv, and Sci-Hub (optional). Designed for seamless integration with large language models like Claude Desktop.

![PyPI](https://img.shields.io/pypi/v/paper-search-mcp.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
[![smithery badge](https://smithery.ai/badge/@openags/paper-search-mcp)](https://smithery.ai/server/@openags/paper-search-mcp)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
  - [Quick Start](#quick-start)
    - [Install Package](#install-package)
    - [Configure Claude Desktop](#configure-claude-desktop)
  - [For Development](#for-development)
    - [Setup Environment](#setup-environment)
    - [Install Dependencies](#install-dependencies)
- [Usage](#usage)
  - [Command Line Flags](#command-line-flags)
  - [Server Modes](#server-modes)
- [API Keys](#api-keys)
- [Contributing](#contributing)
- [Demo](#demo)
- [License](#license)
- [TODO](#todo)

---

## Overview

`paper-search-mcp` is a Python-based MCP server that enables users to search and download academic papers from various platforms. It provides tools for searching papers (e.g., `search_arxiv`) and downloading PDFs (e.g., `download_arxiv`), making it ideal for researchers and AI-driven workflows. Built with the MCP Python SDK, it integrates seamlessly with LLM clients like Claude Desktop.

---

## Features

- **Multi-Source Support**: Search and download papers from arXiv, PubMed, bioRxiv, medRxiv, Google Scholar, IACR ePrint Archive, Semantic Scholar.
- **Standardized Output**: Papers are returned in a consistent dictionary format via the `Paper` class.
- **Dual Transport Modes**: Run as HTTP server (default) or stdio server (for MCP clients).
- **Command Line Configuration**: Configure server behavior via command line flags.
- **API Key Support**: Enhanced functionality with optional API keys (NCBI, Semantic Scholar).
- **Asynchronous Tools**: Efficiently handles network requests using `httpx`.
- **MCP Integration**: Compatible with MCP clients for LLM context enhancement.
- **Extensible Design**: Easily add new academic platforms by extending the `academic_platforms` module.

---

## Installation

`paper-search-mcp` can be installed using `uv` or `pip`. Below are two approaches: a quick start for immediate use and a detailed setup for development.

### Installing via Smithery

To install paper-search-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@openags/paper-search-mcp):

```bash
npx -y @smithery/cli install @openags/paper-search-mcp --client claude
```

### Quick Start

For users who want to quickly run the server:

1. **Install Package**:

   ```bash
   uv add paper-search-mcp
   ```

2. **Configure Claude Desktop**:
   Add this configuration to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):
   ```json
   {
     "mcpServers": {
       "paper_search_server": {
         "command": "uv",
         "args": [
           "run",
           "--directory",
           "/path/to/your/paper-search-mcp",
           "-m",
           "paper_search_mcp.server",
           "--stdio"
         ],
         "env": {
           "NCBI_API_KEY": "", // Optional: For enhanced PubMed access
           "SEMANTIC_SCHOLAR_API_KEY": "" // Optional: For enhanced Semantic Scholar features
         }
       }
     }
   }
   ```
   > Note: Replace `/path/to/your/paper-search-mcp` with your actual installation path. The `--stdio` flag is required for Claude Desktop integration.

### For Development

For developers who want to modify the code or contribute:

1. **Setup Environment**:

   ```bash
   # Install uv if not installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Clone repository
   git clone https://github.com/openags/paper-search-mcp.git
   cd paper-search-mcp

   # Create and activate virtual environment
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**:

   ```bash
   # Install project in editable mode
   uv add -e .

   # Add development dependencies (optional)
   uv add pytest flake8
   ```

---

## Usage

### Command Line Flags

The server supports the following command line options:

```bash
# Run as HTTP server (default)
python -m paper_search_mcp.server

# Run as HTTP server with custom port
python -m paper_search_mcp.server --port 3000

# Run as HTTP server with custom host and port
python -m paper_search_mcp.server --host localhost --port 8080

# Run as stdio server (for MCP clients like Claude Desktop)
python -m paper_search_mcp.server --stdio

# Show help
python -m paper_search_mcp.server --help
```

| Flag | Description | Default | Example |
|------|-------------|---------|---------|
| `--stdio` | Run as stdio server instead of HTTP server | `false` | `--stdio` |
| `--host` | Host address for HTTP server | `0.0.0.0` | `--host localhost` |
| `--port` | Port for HTTP server | `8000` | `--port 3000` |

### Server Modes

**HTTP Server Mode (Default)**:
- Accessible via HTTP requests
- Useful for web integration, testing, or direct API access
- Starts automatically without any flags

**Stdio Mode**:
- Used by MCP clients like Claude Desktop
- Communication via standard input/output
- Requires `--stdio` flag

---

## API Keys

API keys are configured via environment variables:

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `NCBI_API_KEY` | API key for NCBI/PubMed (optional) | [NCBI Account](https://account.ncbi.nlm.nih.gov/) |
| `SEMANTIC_SCHOLAR_API_KEY` | API key for Semantic Scholar (optional) | [Semantic Scholar API](https://www.semanticscholar.org/product/api) |

### NCBI API Key (PubMed)

Getting an NCBI API key improves PubMed search performance:

1. Create account at [NCBI](https://account.ncbi.nlm.nih.gov/)
2. Generate API key in account settings
3. Set `NCBI_API_KEY` environment variable

**Benefits**:
- Higher rate limits (10 requests/second vs 3/second)
- Better performance and reliability
- Reduced throttling

### Semantic Scholar API Key

For enhanced Semantic Scholar functionality:

1. Request API key from [Semantic Scholar](https://www.semanticscholar.org/product/api)
2. Set `SEMANTIC_SCHOLAR_API_KEY` environment variable

**Benefits**:
- Higher rate limits
- Access to additional paper metadata
- Priority support

### Setting Environment Variables

**Windows:**
```bash
set NCBI_API_KEY=your_api_key
set SEMANTIC_SCHOLAR_API_KEY=your_s2_api_key
python -m paper_search_mcp.server
```

**macOS/Linux:**
```bash
export NCBI_API_KEY=your_api_key
export SEMANTIC_SCHOLAR_API_KEY=your_s2_api_key
python -m paper_search_mcp.server
```

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the Repository**:
   Click "Fork" on GitHub.

2. **Clone and Set Up**:

   ```bash
   git clone https://github.com/yourusername/paper-search-mcp.git
   cd paper-search-mcp
   pip install -e ".[dev]"  # Install dev dependencies (if added to pyproject.toml)
   ```

3. **Make Changes**:

   - Add new platforms in `academic_platforms/`.
   - Update tests in `tests/`.

4. **Submit a Pull Request**:
   Push changes and create a PR on GitHub.

---

## Demo

<img src="docs\images\demo.png" alt="Demo" width="800">

## TODO

### Planned Academic Platforms

- [√] arXiv
- [√] PubMed
- [√] bioRxiv
- [√] medRxiv
- [√] Google Scholar
- [√] IACR ePrint Archive
- [√] Semantic Scholar
- [ ] PubMed Central (PMC)
- [ ] Science Direct
- [ ] Springer Link
- [ ] IEEE Xplore
- [ ] ACM Digital Library
- [ ] Web of Science
- [ ] Scopus
- [ ] JSTOR
- [ ] ResearchGate
- [ ] CORE
- [ ] Microsoft Academic

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

Happy researching with `paper-search-mcp`! If you encounter issues, open a GitHub issue.
