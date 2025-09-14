# Agent Discussion Scraper

A web-based tool for scraping and analyzing discussions about multi-agent system challenges across multiple platforms.

## Features

- Multi-platform scraping (Reddit, GitHub, Stack Overflow, Hacker News, ArXiv)
- Granular keyword selection interface
- Real-time progress tracking
- ChatGPT-powered analysis
- Web UI for configuration and monitoring

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Open: http://localhost:5001

## Usage

1. Configure platforms and keywords
2. Run scraping session
3. Analyze results with ChatGPT (requires OpenAI API key)
4. Download insights

## Requirements

- Python 3.9+
- OpenAI API key (for analysis feature)
- GitHub token (optional, for higher rate limits)
