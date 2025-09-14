# Agent Scraper Web UI
# Flask-based interface for controlling the agent discussion scraper

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import threading
import time
from datetime import datetime
from scraper import AgentDiscussionScraper, RedditScraper, GitHubScraper, StackOverflowScraper, HackerNewsScraper, ArXivScraper, Discussion
from dataclasses import asdict

app = Flask(__name__)

# Global variables to track scraping status
scraping_status = {
    'running': False,
    'progress': 0,
    'current_task': '',
    'total_results': 0,
    'start_time': None,
    'error': None
}

# Global variables to track analysis status
analysis_status = {
    'running': False,
    'progress': 0,
    'current_task': '',
    'result': '',
    'error': None
}

class ConfigurableScraper:
    def __init__(self, config):
        self.config = config
        self.scraper = AgentDiscussionScraper()
        self.results = []
        
        # Override the scraper's search terms with user-selected keywords
        if 'selected_keywords' in config:
            self.scraper.search_terms = {
                'agent_connectivity': config['selected_keywords'].get('agent_connectivity', []),
                'agent_discovery': config['selected_keywords'].get('agent_discovery', []),
                'agent_identity': config['selected_keywords'].get('agent_identity', [])
            }
        
    def run_scraping(self):
        """Run the scraping process with the given configuration"""
        global scraping_status
        
        try:
            scraping_status.update({
                'running': True,
                'progress': 0,
                'current_task': 'Initializing scrapers...',
                'total_results': 0,
                'start_time': datetime.now(),
                'error': None
            })
            
            # Initialize scrapers based on config
            scrapers = {}
            if self.config['platforms']['reddit']['enabled']:
                scrapers['reddit'] = RedditScraper()
            if self.config['platforms']['github']['enabled']:
                scrapers['github'] = GitHubScraper(token=self.config['platforms']['github'].get('token'))
            if self.config['platforms']['stackoverflow']['enabled']:
                scrapers['stackoverflow'] = StackOverflowScraper()
            if self.config['platforms']['hackernews']['enabled']:
                scrapers['hackernews'] = HackerNewsScraper()
            if self.config['platforms']['arxiv']['enabled']:
                scrapers['arxiv'] = ArXivScraper()
            
            total_tasks = self._count_total_tasks()
            completed_tasks = 0
            
            # Scrape Reddit
            if 'reddit' in scrapers:
                subreddits = self.config['platforms']['reddit']['subreddits']
                for subreddit in subreddits:
                    scraping_status['current_task'] = f'Scraping Reddit r/{subreddit}'
                    
                    for category, keywords in self.scraper.search_terms.items():
                        if not self.config['search_categories'][category]:
                            continue
                        
                        if not keywords:  # Skip if no keywords selected for this category
                            continue
                            
                        for keyword in keywords:
                            posts = scrapers['reddit'].search_subreddit(
                                subreddit, keyword, 
                                limit=self.config['search_depth']['results_per_search']
                            )
                            
                            self._process_results(posts, f"Reddit r/{subreddit}")
                            completed_tasks += 1
                            scraping_status['progress'] = min(int((completed_tasks / total_tasks) * 100), 100)
                            scraping_status['total_results'] = len(self.results)
            
            # Scrape GitHub
            if 'github' in scrapers:
                scraping_status['current_task'] = 'Scraping GitHub Issues'
                
                for category, keywords in self.scraper.search_terms.items():
                    if not self.config['search_categories'][category]:
                        continue
                    
                    if not keywords:  # Skip if no keywords selected
                        continue
                    
                    # Create search query from selected keywords
                    query = ' OR '.join(keywords[:6])  # Limit to avoid too long queries
                    
                    # Search issues
                    issues = scrapers['github'].search_issues(
                        query, limit=self.config['search_depth']['results_per_search']
                    )
                    self._process_results(issues, "GitHub Issues")
                    
                    # Search repositories
                    scraping_status['current_task'] = 'Scraping GitHub Repositories'
                    repos = scrapers['github'].search_repositories(
                        query, limit=self.config['search_depth']['results_per_search'] // 2
                    )
                    self._process_results(repos, "GitHub Repos")
                    
                    completed_tasks += 1
                    scraping_status['progress'] = min(int((completed_tasks / total_tasks) * 100), 100)
                    scraping_status['total_results'] = len(self.results)
            
            # Scrape Stack Overflow
            if 'stackoverflow' in scrapers:
                scraping_status['current_task'] = 'Scraping Stack Overflow'
                
                for category, keywords in self.scraper.search_terms.items():
                    if not self.config['search_categories'][category]:
                        continue
                    
                    if not keywords:
                        continue
                        
                    for keyword in keywords[:3]:  # Limit to top 3 keywords per category
                        questions = scrapers['stackoverflow'].search_questions(
                            keyword, limit=15
                        )
                        self._process_results(questions, "Stack Overflow")
                        
                    completed_tasks += 1
                    scraping_status['progress'] = min(int((completed_tasks / total_tasks) * 100), 100)
                    scraping_status['total_results'] = len(self.results)
            
            # Scrape Hacker News
            if 'hackernews' in scrapers:
                scraping_status['current_task'] = 'Scraping Hacker News'
                
                for category, keywords in self.scraper.search_terms.items():
                    if not self.config['search_categories'][category]:
                        continue
                    
                    if not keywords:
                        continue
                        
                    for keyword in keywords[:3]:  # Limit to top 3 keywords per category
                        stories = scrapers['hackernews'].search_stories(
                            keyword, limit=15
                        )
                        self._process_results(stories, "Hacker News")
                        
                    completed_tasks += 1
                    scraping_status['progress'] = min(int((completed_tasks / total_tasks) * 100), 100)
                    scraping_status['total_results'] = len(self.results)
            
            # Scrape ArXiv
            if 'arxiv' in scrapers:
                scraping_status['current_task'] = 'Scraping ArXiv'
                
                for category, keywords in self.scraper.search_terms.items():
                    if not self.config['search_categories'][category]:
                        continue
                    
                    if not keywords:
                        continue
                        
                    # Combine keywords for academic search
                    academic_query = ' '.join(keywords[:2])  # Academic searches work better with combined terms
                    papers = scrapers['arxiv'].search_papers(academic_query, limit=10)
                    self._process_results(papers, "ArXiv")
                    
                    completed_tasks += 1
                    scraping_status['progress'] = min(int((completed_tasks / total_tasks) * 100), 100)
                    scraping_status['total_results'] = len(self.results)
            
            # Remove duplicates and save results
            self._finalize_results()
            
            scraping_status.update({
                'running': False,
                'progress': 100,
                'current_task': 'Completed successfully',
                'total_results': len(self.results)
            })
            
        except Exception as e:
            scraping_status.update({
                'running': False,
                'error': str(e),
                'current_task': f'Error: {str(e)}'
            })
    
    def _process_results(self, items, platform):
        """Process scraped items and add relevant ones to results"""
        for item in items:
            relevance, matched = self.scraper.calculate_relevance(
                item['content'], item['title']
            )
            
            if relevance >= self.config['relevance_threshold']:
                discussion = Discussion(
                    title=item['title'],
                    content=item['content'][:500],
                    url=item['url'],
                    platform=platform,
                    author=item['author'],
                    created_at=item['created_at'],
                    score=item['score'],
                    comments_count=item['comments_count'],
                    relevance_score=relevance,
                    keywords_matched=matched
                )
                self.results.append(discussion)
    
    def _count_total_tasks(self):
        """Count total number of scraping tasks for progress tracking"""
        total = 0
        
        # Count Reddit tasks
        if self.config['platforms']['reddit']['enabled']:
            subreddit_count = len(self.config['platforms']['reddit']['subreddits'])
            enabled_categories = sum(self.config['search_categories'].values())
            total += subreddit_count * enabled_categories
        
        # Count GitHub tasks (issues + repos = 1 task per category)
        if self.config['platforms']['github']['enabled']:
            total += sum(self.config['search_categories'].values())
        
        # Count other platform tasks
        if self.config['platforms']['stackoverflow']['enabled']:
            total += sum(self.config['search_categories'].values())
        
        if self.config['platforms']['hackernews']['enabled']:
            total += sum(self.config['search_categories'].values())
        
        if self.config['platforms']['arxiv']['enabled']:
            total += sum(self.config['search_categories'].values())
        
        return max(total, 1)
    
    def _finalize_results(self):
        """Remove duplicates and save results"""
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in self.results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        self.results = unique_results
        self.results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Save to specified file
        results_data = [asdict(d) for d in self.results]
        for result in results_data:
            result['created_at'] = result['created_at'].isoformat()
        
        output_path = self.config['output_file']
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)

def analyze_with_chatgpt(json_data, prompt, api_key):
    """Analyze scraped data using ChatGPT"""
    global analysis_status
    
    try:
        analysis_status.update({
            'running': True,
            'progress': 10,
            'current_task': 'Initializing ChatGPT analysis...',
            'result': '',
            'error': None
        })
        
        # Set up OpenAI client (updated for new API)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        analysis_status['current_task'] = 'Preparing data for analysis...'
        analysis_status['progress'] = 25
        
        # Convert JSON data to string for prompt
        json_string = json.dumps(json_data, indent=2)
        
        # Truncate if too large (ChatGPT has token limits)
        if len(json_string) > 80000:  # Rough token limit check
            analysis_status['current_task'] = 'Data too large, analyzing summary...'
            # Create a summary version with key fields only
            summary_data = []
            for item in json_data[:50]:  # Take first 50 items
                summary_data.append({
                    'title': item.get('title', ''),
                    'platform': item.get('platform', ''),
                    'relevance_score': item.get('relevance_score', 0),
                    'keywords_matched': item.get('keywords_matched', []),
                    'content': item.get('content', '')[:200]  # Truncate content
                })
            json_string = json.dumps(summary_data, indent=2)
        
        analysis_status['current_task'] = 'Sending request to ChatGPT...'
        analysis_status['progress'] = 50
        
        # Create the full prompt
        full_prompt = f"{prompt}\n\nJSON Data:\n{json_string}"
        
        # Make the API call (updated format)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use more affordable model
            messages=[
                {"role": "system", "content": "You are an expert analyst specializing in developer tools and multi-agent systems. Provide detailed, structured analysis with clear insights."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        analysis_status['current_task'] = 'Processing results...'
        analysis_status['progress'] = 90
        
        result = response.choices[0].message.content
        
        analysis_status.update({
            'running': False,
            'progress': 100,
            'current_task': 'Analysis completed',
            'result': result
        })
        
    except Exception as e:
        print(f"DEBUG: Analysis error: {e}")  # Debug print
        analysis_status.update({
            'running': False,
            'error': str(e),
            'current_task': f'Error: {str(e)}'
        })

@app.route('/')
def index():
    """Main page with scraper configuration form"""
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process with user configuration"""
    global scraping_status
    
    if scraping_status['running']:
        return jsonify({'success': False, 'error': 'Scraping already in progress'})
    
    try:
        config = request.json
        print(f"DEBUG: Received config: {config}")
        
        # Validate configuration
        if not config.get('output_file'):
            return jsonify({'success': False, 'error': 'Output file path is required'})
        
        # Validate that at least some keywords are selected
        selected_keywords = config.get('selected_keywords', {})
        total_keywords = sum(len(keywords) for keywords in selected_keywords.values())
        
        if total_keywords == 0:
            return jsonify({'success': False, 'error': 'Please select at least one keyword'})
        
        # Create and start scraper in background thread
        configurable_scraper = ConfigurableScraper(config)
        scraping_thread = threading.Thread(target=configurable_scraper.run_scraping)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        return jsonify({'success': True, 'message': 'Scraping started'})
        
    except Exception as e:
        print(f"DEBUG: Error in start_scraping: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status')
def get_status():
    """Get current scraping status"""
    status = scraping_status.copy()
    if status['start_time']:
        elapsed = datetime.now() - status['start_time']
        status['elapsed_time'] = str(elapsed).split('.')[0]
    return jsonify(status)

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    """Stop the current scraping process"""
    global scraping_status
    scraping_status.update({
        'running': False,
        'current_task': 'Stopped by user',
        'error': 'Stopped by user'
    })
    return jsonify({'success': True, 'message': 'Scraping stopped'})

@app.route('/analyze_results', methods=['POST'])
def analyze_results():
    """Start ChatGPT analysis of scraping results"""
    global analysis_status
    
    if analysis_status['running']:
        return jsonify({'success': False, 'error': 'Analysis already in progress'})
    
    try:
        data = request.json
        json_file_path = data.get('json_file_path')
        prompt = data.get('prompt')
        api_key = data.get('api_key')
        
        if not json_file_path or not prompt or not api_key:
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        # Check if the specified file exists, if not, look for alternatives
        if not os.path.exists(json_file_path):
            # Look for any JSON files in the current directory
            json_files = [f for f in os.listdir('.') if f.endswith('.json') and 'agent' in f.lower()]
            
            if json_files:
                # Use the most recent JSON file
                json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                json_file_path = json_files[0]
                print(f"DEBUG: Using alternative JSON file: {json_file_path}")
            else:
                return jsonify({'success': False, 'error': f'No JSON file found. Available files: {os.listdir(".")}'})
        
        # Load the JSON data
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
        
        if not json_data:
            return jsonify({'success': False, 'error': 'JSON file is empty'})
        
        print(f"DEBUG: Loaded {len(json_data)} items from {json_file_path}")
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(target=analyze_with_chatgpt, args=(json_data, prompt, api_key))
        analysis_thread.daemon = True
        analysis_thread.start()
        
        return jsonify({'success': True, 'message': f'Analysis started using {json_file_path}'})
        
    except Exception as e:
        print(f"DEBUG: Error in analyze_results: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analysis_status')
def get_analysis_status():
    """Get current analysis status"""
    return jsonify(analysis_status)

@app.route('/save_analysis', methods=['POST'])
def save_analysis():
    """Save analysis results to a text file"""
    try:
        data = request.json
        filename = data.get('filename', 'analysis_results.txt')
        content = data.get('content', '')
        
        if not content:
            return jsonify({'success': False, 'error': 'No content to save'})
        
        # Ensure filename ends with .txt
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        with open(filename, 'w') as f:
            f.write(content)
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        print(f"DEBUG: Error in save_analysis: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/list_json_files')
def list_json_files():
    """List available JSON files in the current directory"""
    try:
        json_files = []
        for filename in os.listdir('.'):
            if filename.endswith('.json') and ('agent' in filename.lower() or 'discussions' in filename.lower()):
                file_path = filename
                file_size = os.path.getsize(file_path)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                json_files.append({
                    'filename': filename,
                    'size': file_size,
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modification time, newest first
        json_files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': json_files})
        
    except Exception as e:
        print(f"DEBUG: Error in list_json_files: {e}")
        return jsonify({'error': str(e)})

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download the generated JSON file"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)