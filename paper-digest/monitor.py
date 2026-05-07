import os
import json
import time
import yaml
import smtplib
import requests
import anthropic
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as f:
        return yaml.safe_load(f)


def get_s2_headers():
    """Return Semantic Scholar API headers if key is available."""
    api_key = os.environ.get('S2_API_KEY', '')
    return {'x-api-key': api_key} if api_key else {}


def s2_get(url, params, retries=3):
    """GET request to Semantic Scholar with retry on rate limit."""
    headers = get_s2_headers()
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"Rate limited — waiting {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                print(f"HTTP {resp.status_code} from Semantic Scholar")
                return None
        except Exception as e:
            print(f"Request error: {e}")
            time.sleep(5)
    return None


def fetch_papers_by_keywords(config):
    """Search Semantic Scholar by keyword."""
    papers = {}
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')

    for keyword in config.get('keywords', []):
        params = {
            'query': keyword,
            'fields': 'paperId,title,abstract,authors,year,publicationDate,venue,citationCount,url',
            'publicationDateOrYear': f'{two_weeks_ago}:{today}',
            'limit': 25,
        }
        resp = s2_get("https://api.semanticscholar.org/graph/v1/paper/search", params)
        if resp:
            for paper in resp.json().get('data', []):
                if not paper.get('abstract'):
                    continue
                pid = paper['paperId']
                if pid not in papers:
                    papers[pid] = paper
            print(f"  '{keyword}' → {len(resp.json().get('data', []))} papers")
        time.sleep(1.5)

    return papers


def fetch_papers_by_authors(config):
    """Fetch recent papers by tracked authors regardless of journal."""
    papers = {}
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')

    for author_name in config.get('authors_to_track', []):
        try:
            # Step 1: resolve author ID
            resp = s2_get(
                "https://api.semanticscholar.org/graph/v1/author/search",
                {'query': author_name, 'limit': 3},
            )
            time.sleep(1.5)
            if not resp or not resp.json().get('data'):
                print(f"Author not found: {author_name}")
                continue

            author_id = resp.json()['data'][0]['authorId']
            print(f"  Found author '{author_name}' — id {author_id}")

            # Step 2: get their papers
            resp2 = s2_get(
                f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers",
                {
                    'fields': 'paperId,title,abstract,authors,year,publicationDate,venue,citationCount,url',
                    'limit': 20,
                },
            )
            time.sleep(1.5)
            if not resp2:
                continue

            for paper in resp2.json().get('data', []):
                pub_date = paper.get('publicationDate') or ''
                if pub_date >= two_weeks_ago and paper.get('abstract'):
                    pid = paper['paperId']
                    if pid not in papers:
                        paper['tracked_author'] = author_name
                        papers[pid] = paper

        except Exception as e:
            print(f"Error fetching papers for author '{author_name}': {e}")

    return papers


def get_journal_weight(paper, config):
    venue = (paper.get('venue') or '').lower()
    for j in config.get('journals', []):
        if j['name'].lower() in venue:
            return j.get('weight', 1.0)
    return 1.0


def score_and_summarize(papers_dict, config):
    """Use Claude Haiku to score and summarize each paper."""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    research_desc = config['research_profile']['description']
    min_score = config['delivery'].get('min_relevance_score', 6)
    results = []

    for paper in papers_dict.values():
        title = paper.get('title', 'N/A')
        abstract = paper.get('abstract', '')
        authors_str = ', '.join(a.get('name', '') for a in paper.get('authors', [])[:4])
        if len(paper.get('authors', [])) > 4:
            authors_str += ' et al.'

        prompt = f"""You are a research assistant helping a PhD researcher track literature.

Research focus:
{research_desc}

Paper:
Title: {title}
Authors: {authors_str}
Venue: {paper.get('venue', 'N/A')}
Year: {paper.get('year', 'N/A')}
Abstract: {abstract}

Tasks:
1. Score relevance 1-10 (10 = directly addresses the research focus)
2. Write a 2-3 sentence plain-language summary of the paper's contribution
3. One sentence explaining why it is or is not relevant to this research

Respond with valid JSON only:
{{"score": <int>, "summary": "<str>", "relevance_reason": "<str>"}}"""

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=350,
                messages=[{"role": "user", "content": prompt}],
            )
            data = json.loads(response.content[0].text)
            raw_score = data.get('score', 0)

            # Apply journal weight boost
            weight = get_journal_weight(paper, config)
            boosted_score = min(10, round(raw_score * weight, 1))

            if boosted_score >= min_score:
                paper['score'] = boosted_score
                paper['raw_score'] = raw_score
                paper['summary'] = data.get('summary', '')
                paper['relevance_reason'] = data.get('relevance_reason', '')
                results.append(paper)

        except Exception as e:
            print(f"Error scoring '{title}': {e}")

        time.sleep(0.5)

    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results


def build_html(papers, config):
    today = datetime.now().strftime('%B %d, %Y')
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%B %d, %Y')

    high = [p for p in papers if p.get('score', 0) >= 8]
    medium = [p for p in papers if 6 <= p.get('score', 0) < 8]

    def card(paper):
        authors = ', '.join(a.get('name', '') for a in paper.get('authors', [])[:3])
        if len(paper.get('authors', [])) > 3:
            authors += ' et al.'
        url = paper.get('url') or '#'
        tracked = f' <span style="color:#2c5f8a; font-size:11px;">★ Tracked author: {paper["tracked_author"]}</span>' if paper.get('tracked_author') else ''
        return f"""
        <div style="margin-bottom:18px;padding:14px 16px;border-left:3px solid #2c5f8a;background:#f8f9fa;border-radius:2px;">
          <h3 style="margin:0 0 4px 0;font-size:15px;">
            <a href="{url}" style="color:#2c5f8a;text-decoration:none;">{paper.get('title','N/A')}</a>
            <span style="font-weight:normal;color:#888;font-size:12px;"> — {paper.get('score')}/10</span>
            {tracked}
          </h3>
          <p style="margin:2px 0;color:#666;font-size:12px;">{authors} | {paper.get('venue','N/A')} | {paper.get('year','N/A')}</p>
          <p style="margin:8px 0 4px 0;font-size:14px;">{paper.get('summary','')}</p>
          <p style="margin:0;color:#888;font-size:12px;font-style:italic;">{paper.get('relevance_reason','')}</p>
        </div>"""

    sections = ''
    if high:
        sections += f'<h2 style="color:#1a5c1a;margin-top:24px;">High Relevance — {len(high)} paper{"s" if len(high)>1 else ""}</h2>'
        for p in high:
            sections += card(p)
    if medium:
        sections += f'<h2 style="color:#8a6c2c;margin-top:24px;">Moderate Relevance — {len(medium)} paper{"s" if len(medium)>1 else ""}</h2>'
        for p in medium:
            sections += card(p)
    if not papers:
        sections = '<p style="color:#666;">No new relevant papers found this period.</p>'

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:680px;margin:auto;padding:24px;color:#333;">
      <h1 style="color:#2c5f8a;border-bottom:2px solid #2c5f8a;padding-bottom:8px;margin-bottom:4px;">
        Research Digest
      </h1>
      <p style="color:#888;margin-top:0;font-size:13px;">{two_weeks_ago} → {today} &nbsp;|&nbsp; {len(papers)} relevant papers</p>
      {sections}
      <hr style="border:none;border-top:1px solid #eee;margin-top:32px;">
      <p style="color:#bbb;font-size:11px;">
        Semantic Scholar + Claude Haiku &nbsp;|&nbsp; Edit <code>config.yaml</code> to adjust journals, keywords, or authors.
      </p>
    </body></html>"""


def send_email(html, config):
    sender = os.environ['GMAIL_ADDRESS']
    password = os.environ['GMAIL_APP_PASSWORD']
    recipient = config['delivery']['email']
    today = datetime.now().strftime('%B %d, %Y')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Research Digest — {today}'
    msg['From'] = sender
    msg['To'] = recipient
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Digest sent to {recipient}")


def main():
    config = load_config()

    print("Fetching papers by keyword...")
    keyword_papers = fetch_papers_by_keywords(config)
    print(f"  {len(keyword_papers)} unique papers from keyword searches")

    print("Fetching papers by tracked authors...")
    author_papers = fetch_papers_by_authors(config)
    print(f"  {len(author_papers)} papers from tracked authors")

    all_papers = {**keyword_papers, **author_papers}
    print(f"Total unique papers to score: {len(all_papers)}")

    print("Scoring and summarizing with Claude...")
    scored = score_and_summarize(all_papers, config)
    print(f"{len(scored)} papers above relevance threshold — building digest...")

    html = build_html(scored, config)
    send_email(html, config)


if __name__ == '__main__':
    main()
