# Agent Discussion Scraper - Expanded Version
# Finds discussions about agent connectivity, discovery, and identity challenges

import requests
import time
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re
from urllib.parse import quote

@dataclass
class Discussion:
    title: str
    content: str
    url: str
    platform: str
    author: str
    created_at: datetime
    score: int
    comments_count: int
    relevance_score: float = 0.0
    keywords_matched: List[str] = None

class AgentDiscussionScraper:
    def __init__(self):
        self.search_terms = {
            'agent_connectivity': [
                'agent to agent', 'A2A protocol', 'MCP', 'multi-agent communication',
                'agent messaging', 'inter-agent', 'agent network', 'agent coordination',
                'agent orchestration', 'agent workflow', 'agent collaboration', 'cross-agent',
                'agent bridge', 'agent proxy', 'agent middleware', 'agent bus'
            ],
            'agent_discovery': [
                'agent registry', 'agent discovery', 'fleet management', 'agent marketplace',
                'agent directory', 'service discovery', 'agent catalog', 'agent inventory',
                'agent lookup', 'agent routing', 'agent broker', 'agent mesh',
                'dynamic agent discovery', 'agent topology', 'agent federation'
            ],
            'agent_identity': [
                'agent identity', 'agent authentication', 'zero trust agents', 'agent authorization',
                'agent credentials', 'agent security', 'agent access control', 'agent PKI',
                'agent certificates', 'agent tokens', 'agent permissions', 'agent roles',
                'agent delegation', 'agent trust', 'agent verification', 'agent compliance'
            ]
        }
        
        self.results = []
        
    def calculate_relevance(self, text: str, title: str) -> tuple[float, List[str]]:
        """Calculate relevance score based on keyword matches and context"""
        text_lower = (text + " " + title).lower()
        matched_keywords = []
        score = 0.0
        
        # Check for exact keyword matches
        for category, keywords in self.search_terms.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
                    # Weight by category importance and keyword specificity
                    if category == 'agent_connectivity':
                        score += 2.0
                    elif category == 'agent_discovery':
                        score += 1.8
                    elif category == 'agent_identity':
                        score += 1.5
        
        # Boost for technical implementation discussions
        tech_indicators = ['implementation', 'protocol', 'API', 'framework', 'architecture']
        for indicator in tech_indicators:
            if indicator.lower() in text_lower:
                score += 0.5
        
        # Boost for problem/challenge discussions
        problem_indicators = ['problem', 'challenge', 'issue', 'difficulty', 'pain point']
        for indicator in problem_indicators:
            if indicator.lower() in text_lower:
                score += 0.3
                
        return score, matched_keywords

class RedditScraper:
    def __init__(self, user_agent: str = "AgentDiscussionScraper/1.0"):
        self.base_url = "https://www.reddit.com"
        self.headers = {'User-Agent': user_agent}
        
    def search_subreddit(self, subreddit: str, query: str, limit: int = 25) -> List[Dict]:
        """Search a specific subreddit for posts"""
        url = f"{self.base_url}/r/{subreddit}/search.json"
        params = {
            'q': query,
            'restrict_sr': 'on',
            'sort': 'relevance',
            'limit': limit,
            't': 'year'  # Past year
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(1)  # Be respectful
            
            data = response.json()
            posts = []
            
            for post in data['data']['children']:
                post_data = post['data']
                posts.append({
                    'title': post_data.get('title', ''),
                    'content': post_data.get('selftext', ''),
                    'url': f"{self.base_url}{post_data.get('permalink', '')}",
                    'author': post_data.get('author', ''),
                    'created_at': datetime.fromtimestamp(post_data.get('created_utc', 0)),
                    'score': post_data.get('score', 0),
                    'comments_count': post_data.get('num_comments', 0)
                })
            
            return posts
            
        except Exception as e:
            print(f"Error scraping Reddit r/{subreddit}: {e}")
            return []

class GitHubScraper:
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def search_issues(self, query: str, limit: int = 50) -> List[Dict]:
        """Search GitHub issues and discussions"""
        url = f"{self.base_url}/search/issues"
        params = {
            'q': f'{query} type:issue',
            'sort': 'updated',
            'order': 'desc',
            'per_page': min(limit, 100)
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(1)  # Rate limiting
            
            data = response.json()
            issues = []
            
            for item in data.get('items', []):
                issues.append({
                    'title': item.get('title', ''),
                    'content': item.get('body', '') or '',
                    'url': item.get('html_url', ''),
                    'author': item.get('user', {}).get('login', ''),
                    'created_at': datetime.fromisoformat(item.get('created_at', '').replace('Z', '+00:00')),
                    'score': item.get('reactions', {}).get('total_count', 0),
                    'comments_count': item.get('comments', 0)
                })
            
            return issues
            
        except Exception as e:
            print(f"Error scraping GitHub: {e}")
            return []
    
    def search_repositories(self, query: str, limit: int = 20) -> List[Dict]:
        """Search GitHub repositories for agent infrastructure projects"""
        url = f"{self.base_url}/search/repositories"
        params = {
            'q': f'{query} language:python OR language:typescript OR language:rust',
            'sort': 'updated',
            'order': 'desc',
            'per_page': min(limit, 100)
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(1)
            
            data = response.json()
            repos = []
            
            for item in data.get('items', []):
                repos.append({
                    'title': f"Repository: {item.get('name', '')}",
                    'content': item.get('description', '') or '',
                    'url': item.get('html_url', ''),
                    'author': item.get('owner', {}).get('login', ''),
                    'created_at': datetime.fromisoformat(item.get('updated_at', '').replace('Z', '+00:00')),
                    'score': item.get('stargazers_count', 0),
                    'comments_count': item.get('open_issues_count', 0)
                })
            
            return repos
            
        except Exception as e:
            print(f"Error scraping GitHub repos: {e}")
            return []

class StackOverflowScraper:
    def __init__(self):
        self.base_url = "https://api.stackexchange.com/2.3"
        
    def search_questions(self, query: str, limit: int = 30) -> List[Dict]:
        """Search Stack Overflow questions"""
        url = f"{self.base_url}/search/advanced"
        params = {
            'order': 'desc',
            'sort': 'activity',
            'q': query,
            'site': 'stackoverflow',
            'pagesize': min(limit, 100),
            'filter': 'withbody'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            time.sleep(1)
            
            data = response.json()
            questions = []
            
            for item in data.get('items', []):
                questions.append({
                    'title': item.get('title', ''),
                    'content': item.get('body', '')[:500],  # Truncate
                    'url': item.get('link', ''),
                    'author': item.get('owner', {}).get('display_name', 'Anonymous'),
                    'created_at': datetime.fromtimestamp(item.get('creation_date', 0)),
                    'score': item.get('score', 0),
                    'comments_count': item.get('answer_count', 0)
                })
            
            return questions
            
        except Exception as e:
            print(f"Error scraping Stack Overflow: {e}")
            return []

class HackerNewsScraper:
    def __init__(self):
        self.base_url = "https://hn.algolia.com/api/v1"
        
    def search_stories(self, query: str, limit: int = 30) -> List[Dict]:
        """Search Hacker News stories and comments"""
        url = f"{self.base_url}/search"
        params = {
            'query': query,
            'tags': 'story',
            'hitsPerPage': min(limit, 50),
            'numericFilters': f'created_at_i>{int((datetime.now() - timedelta(days=365)).timestamp())}'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            time.sleep(1)
            
            data = response.json()
            stories = []
            
            for item in data.get('hits', []):
                stories.append({
                    'title': item.get('title', ''),
                    'content': item.get('story_text', '') or item.get('url', ''),
                    'url': f"https://news.ycombinator.com/item?id={item.get('objectID', '')}",
                    'author': item.get('author', ''),
                    'created_at': datetime.fromisoformat(item.get('created_at', '').replace('Z', '+00:00')),
                    'score': item.get('points', 0),
                    'comments_count': item.get('num_comments', 0)
                })
            
            return stories
            
        except Exception as e:
            print(f"Error scraping Hacker News: {e}")
            return []

class ArXivScraper:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        
    def search_papers(self, query: str, limit: int = 20) -> List[Dict]:
        """Search ArXiv papers"""
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': min(limit, 50),
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            time.sleep(1)
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title')
                summary = entry.find('{http://www.w3.org/2005/Atom}summary')
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                author = entry.find('.//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name')
                published = entry.find('{http://www.w3.org/2005/Atom}published')
                
                papers.append({
                    'title': title.text if title is not None else '',
                    'content': (summary.text if summary is not None else '')[:500],
                    'url': link.get('href') if link is not None else '',
                    'author': author.text if author is not None else '',
                    'created_at': datetime.fromisoformat(published.text.replace('Z', '+00:00')) if published is not None else datetime.now(),
                    'score': 0,  # ArXiv doesn't have scores
                    'comments_count': 0
                })
            
            return papers
            
        except Exception as e:
            print(f"Error scraping ArXiv: {e}")
            return []

def main():
    scraper = AgentDiscussionScraper()
    reddit = RedditScraper()
    github = GitHubScraper()  # Add your GitHub token here if you have one
    stackoverflow = StackOverflowScraper()
    hackernews = HackerNewsScraper()
    arxiv = ArXivScraper()
    
    # Expanded target subreddits
    subreddits = [
        'MachineLearning', 'artificial', 'programming', 'LocalLLaMA', 
        'singularity', 'compsci', 'MachineLearningNews', 'ArtificialIntelligence',
        'deeplearning', 'ChatGPT', 'OpenAI', 'reinforcementlearning'
    ]
    
    print("🔍 Starting expanded agent discussion scrape...")
    
    # Scrape Reddit - Increased depth
    print("\n📱 Scraping Reddit...")
    for subreddit in subreddits:
        print(f"  📍 Searching r/{subreddit}")
        for category, keywords in scraper.search_terms.items():
            # Use more keywords and get more results per search
            for keyword in keywords[:4]:  # Top 4 keywords per category (increased from 2)
                posts = reddit.search_subreddit(subreddit, keyword, limit=20)  # Increased from 10
                
                for post in posts:
                    relevance, matched = scraper.calculate_relevance(
                        post['content'], post['title']
                    )
                    
                    if relevance > 0.3:  # Lowered threshold to catch more results
                        discussion = Discussion(
                            title=post['title'],
                            content=post['content'][:500],
                            url=post['url'],
                            platform=f"Reddit r/{subreddit}",
                            author=post['author'],
                            created_at=post['created_at'],
                            score=post['score'],
                            comments_count=post['comments_count'],
                            relevance_score=relevance,
                            keywords_matched=matched
                        )
                        scraper.results.append(discussion)
    
    # Scrape GitHub - Issues and Repositories
    print("\n🐙 Scraping GitHub...")
    for category, keywords in scraper.search_terms.items():
        print(f"  📍 Searching GitHub for {category}")
        # Search issues
        query = ' OR '.join(keywords[:4])  # Top 4 keywords
        issues = github.search_issues(query, limit=25)  # Increased from 15
        
        for issue in issues:
            relevance, matched = scraper.calculate_relevance(
                issue['content'], issue['title']
            )
            
            if relevance > 0.3:
                discussion = Discussion(
                    title=issue['title'],
                    content=issue['content'][:500],
                    url=issue['url'],
                    platform="GitHub Issues",
                    author=issue['author'],
                    created_at=issue['created_at'],
                    score=issue['score'],
                    comments_count=issue['comments_count'],
                    relevance_score=relevance,
                    keywords_matched=matched
                )
                scraper.results.append(discussion)
        
        # Search repositories
        repos = github.search_repositories(query, limit=15)
        for repo in repos:
            relevance, matched = scraper.calculate_relevance(
                repo['content'], repo['title']
            )
            
            if relevance > 0.3:
                discussion = Discussion(
                    title=repo['title'],
                    content=repo['content'][:500],
                    url=repo['url'],
                    platform="GitHub Repos",
                    author=repo['author'],
                    created_at=repo['created_at'],
                    score=repo['score'],
                    comments_count=repo['comments_count'],
                    relevance_score=relevance,
                    keywords_matched=matched
                )
                scraper.results.append(discussion)
    
    # Scrape Stack Overflow
    print("\n📚 Scraping Stack Overflow...")
    for category, keywords in scraper.search_terms.items():
        print(f"  📍 Searching Stack Overflow for {category}")
        for keyword in keywords[:3]:  # Top 3 keywords per category
            questions = stackoverflow.search_questions(keyword, limit=15)
            
            for question in questions:
                relevance, matched = scraper.calculate_relevance(
                    question['content'], question['title']
                )
                
                if relevance > 0.3:
                    discussion = Discussion(
                        title=question['title'],
                        content=question['content'][:500],
                        url=question['url'],
                        platform="Stack Overflow",
                        author=question['author'],
                        created_at=question['created_at'],
                        score=question['score'],
                        comments_count=question['comments_count'],
                        relevance_score=relevance,
                        keywords_matched=matched
                    )
                    scraper.results.append(discussion)
    
    # Scrape Hacker News
    print("\n📰 Scraping Hacker News...")
    for category, keywords in scraper.search_terms.items():
        print(f"  📍 Searching Hacker News for {category}")
        for keyword in keywords[:3]:
            stories = hackernews.search_stories(keyword, limit=15)
            
            for story in stories:
                relevance, matched = scraper.calculate_relevance(
                    story['content'], story['title']
                )
                
                if relevance > 0.3:
                    discussion = Discussion(
                        title=story['title'],
                        content=story['content'][:500],
                        url=story['url'],
                        platform="Hacker News",
                        author=story['author'],
                        created_at=story['created_at'],
                        score=story['score'],
                        comments_count=story['comments_count'],
                        relevance_score=relevance,
                        keywords_matched=matched
                    )
                    scraper.results.append(discussion)
    
    # Scrape ArXiv
    print("\n📖 Scraping ArXiv...")
    for category, keywords in scraper.search_terms.items():
        print(f"  📍 Searching ArXiv for {category}")
        # Combine keywords for academic search
        academic_query = ' '.join(keywords[:2])  # Academic searches work better with combined terms
        papers = arxiv.search_papers(academic_query, limit=10)
        
        for paper in papers:
            relevance, matched = scraper.calculate_relevance(
                paper['content'], paper['title']
            )
            
            if relevance > 0.3:
                discussion = Discussion(
                    title=paper['title'],
                    content=paper['content'][:500],
                    url=paper['url'],
                    platform="ArXiv",
                    author=paper['author'],
                    created_at=paper['created_at'],
                    score=paper['score'],
                    comments_count=paper['comments_count'],
                    relevance_score=relevance,
                    keywords_matched=matched
                )
                scraper.results.append(discussion)
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []
    for result in scraper.results:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            unique_results.append(result)
    
    scraper.results = unique_results
    
    # Sort by relevance and display results
    scraper.results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    print(f"\n✅ Found {len(scraper.results)} unique relevant discussions across all platforms")
    
    # Platform breakdown
    platform_counts = {}
    for result in scraper.results:
        platform_counts[result.platform] = platform_counts.get(result.platform, 0) + 1
    
    print("\n📊 Results by platform:")
    for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {platform}: {count} discussions")
    
    print("\n🏆 Top Results:")
    
    for i, discussion in enumerate(scraper.results[:15], 1):  # Show top 15
        print(f"\n{i}. [{discussion.platform}] {discussion.title}")
        print(f"   Score: {discussion.relevance_score:.1f} | Author: {discussion.author}")
        print(f"   Keywords: {', '.join(discussion.keywords_matched)}")
        print(f"   URL: {discussion.url}")
        if discussion.content.strip():
            print(f"   Preview: {discussion.content[:200]}...")
    
    # Save to JSON for further analysis
    results_data = [asdict(d) for d in scraper.results]
    # Convert datetime objects to strings for JSON serialization
    for result in results_data:
        result['created_at'] = result['created_at'].isoformat()
    
    with open('agent_discussions_expanded.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Results saved to agent_discussions_expanded.json")
    print(f"🎯 Search completed! Found discussions across {len(platform_counts)} platforms")

if __name__ == "__main__":
    main()