import os
import re
import json
import time
import yaml
import smtplib
import requests
import anthropic
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

OPENALEX_BASE = "https://api.openalex.org"
MAILTO = "urialuzon@gmail.com"  # identifies us in OpenAlex polite pool


def load_config():
    with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as f:
        return yaml.safe_load(f)


# ── OpenAlex helpers ──────────────────────────────────────────

def openalex_get(path, params, retries=3):
    """GET from OpenAlex with retry. Adds mailto for polite-pool access."""
    params['mailto'] = MAILTO
    url = f"{OPENALEX_BASE}/{path}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"Rate limited — waiting {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                print(f"OpenAlex HTTP {resp.status_code} for {path}")
                return None
        except Exception as e:
            print(f"Request error: {e}")
            time.sleep(5)
    return None


def reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as word→positions dict. Rebuild to string."""
    if not inverted_index:
        return ''
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return ' '.join(words[i] for i in sorted(words.keys()))


def normalize_paper(work, tracked_author=None):
    """Convert OpenAlex work object to a standard internal dict."""
    abstract = reconstruct_abstract(work.get('abstract_inverted_index') or {})
    authors = [
        {'name': a['author']['display_name']}
        for a in work.get('authorships', [])
        if a.get('author') and a['author'].get('display_name')
    ]
    venue = (
        (work.get('primary_location') or {})
        .get('source') or {}
    ).get('display_name', '') or ''

    url = work.get('doi') or work.get('landing_page_url') or work.get('id') or '#'

    paper = {
        'id': work.get('id', ''),
        'title': work.get('title', 'N/A'),
        'abstract': abstract,
        'authors': authors,
        'venue': venue,
        'year': work.get('publication_year', ''),
        'publication_date': work.get('publication_date', ''),
        'citation_count': work.get('cited_by_count', 0),
        'url': url,
    }
    if tracked_author:
        paper['tracked_author'] = tracked_author
    return paper


# ── Fetching ─────────────────────────────────────────────────

def fetch_papers_by_keywords(config):
    """Search OpenAlex by keyword, filtered to last 2 weeks."""
    papers = {}
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')

    for keyword in config.get('keywords', []):
        params = {
            'search': keyword,
            'filter': f'from_publication_date:{two_weeks_ago}',
            'per-page': 25,
        }
        resp = openalex_get('works', params)
        if resp:
            results = resp.json().get('results', [])
            count = 0
            for work in results:
                paper = normalize_paper(work)
                if paper['abstract'] and paper['id'] not in papers:
                    papers[paper['id']] = paper
                    count += 1
            print(f"  '{keyword}' → {count} papers")
        time.sleep(1.0)

    return papers


def fetch_papers_by_authors(config):
    """Fetch recent papers by tracked authors."""
    papers = {}
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d')

    for author_name in config.get('authors_to_track', []):
        # Step 1: resolve author ID
        resp = openalex_get('authors', {'search': author_name, 'per-page': 1})
        time.sleep(1.0)
        if not resp:
            print(f"  Author lookup failed: {author_name}")
            continue

        results = resp.json().get('results', [])
        if not results:
            print(f"  Author not found: {author_name}")
            continue

        author_id = results[0]['id'].split('/')[-1]  # extract e.g. A123456
        print(f"  Found '{author_name}' → {author_id}")

        # Step 2: get their recent papers
        resp2 = openalex_get('works', {
            'filter': f'authorships.author.id:{author_id},'
                      f'from_publication_date:{two_weeks_ago}',
            'per-page': 10,
        })
        time.sleep(1.0)
        if not resp2:
            continue

        for work in resp2.json().get('results', []):
            paper = normalize_paper(work, tracked_author=author_name)
            if paper['abstract'] and paper['id'] not in papers:
                papers[paper['id']] = paper

    return papers


# ── Scoring ───────────────────────────────────────────────────

def get_journal_weight(paper, config):
    venue = paper.get('venue', '').lower()
    for j in config.get('journals', []):
        if j['name'].lower() in venue:
            return j.get('weight', 1.0)
    return 1.0


def extract_json(text):
    """Try direct parse, then regex-extract first {...} block."""
    text = (text or '').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def score_and_summarize(papers_dict, config):
    """Use Claude Haiku to score and summarize each paper."""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    research_desc = config['research_profile']['description']
    min_score = config['delivery'].get('min_relevance_score', 6)
    results = []

    system_prompt = (
        "You are a research assistant. Respond with valid JSON only — "
        "no preamble, no explanation, no markdown fences. "
        'Output exactly: {"score": <int 1-10>, "summary": "<str>", "relevance_reason": "<str>"}'
    )

    for paper in papers_dict.values():
        title = paper.get('title', 'N/A')
        abstract = paper.get('abstract', '')
        authors_str = ', '.join(a['name'] for a in paper.get('authors', [])[:4])
        if len(paper.get('authors', [])) > 4:
            authors_str += ' et al.'

        prompt = f"""Research focus:
{research_desc}

Paper:
Title: {title}
Authors: {authors_str}
Venue: {paper.get('venue', 'N/A')}
Year: {paper.get('year', 'N/A')}
Abstract: {abstract}

Score relevance 1-10, write a 2-3 sentence summary, and one sentence on relevance.
Return JSON only: {{"score": <int>, "summary": "<str>", "relevance_reason": "<str>"}}"""

        data = None
        for attempt in range(3):
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=400,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_text = response.content[0].text if response.content else ''
                data = extract_json(raw_text)
                if data:
                    break
                print(f"  Attempt {attempt+1}: no JSON in response for '{title[:50]}'")
            except Exception as e:
                print(f"  Attempt {attempt+1} error for '{title[:50]}': {e}")
            time.sleep(1.0)

        if not data:
            print(f"  Skipping '{title[:60]}' — could not parse score after 3 attempts")
            time.sleep(0.5)
            continue

        try:
            raw_score = int(data.get('score', 0))
            weight = get_journal_weight(paper, config)
            boosted_score = min(10, round(raw_score * weight, 1))

            if boosted_score >= min_score:
                paper['score'] = boosted_score
                paper['summary'] = data.get('summary', '')
                paper['relevance_reason'] = data.get('relevance_reason', '')
                results.append(paper)
        except Exception as e:
            print(f"  Score processing error for '{title[:50]}': {e}")

        time.sleep(0.5)

    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results


# ── Email ─────────────────────────────────────────────────────

def build_html(papers, config):
    today = datetime.now().strftime('%B %d, %Y')
    two_weeks_ago = (datetime.now() - timedelta(weeks=2)).strftime('%B %d, %Y')

    high = [p for p in papers if p.get('score', 0) >= 8]
    medium = [p for p in papers if 6 <= p.get('score', 0) < 8]

    def card(paper):
        authors = ', '.join(a['name'] for a in paper.get('authors', [])[:3])
        if len(paper.get('authors', [])) > 3:
            authors += ' et al.'
        url = paper.get('url') or '#'
        tracked = (
            f' <span style="color:#2c5f8a;font-size:11px;">★ {paper["tracked_author"]}</span>'
            if paper.get('tracked_author') else ''
        )
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
        OpenAlex + Claude Haiku &nbsp;|&nbsp; Edit <code>config.yaml</code> to adjust journals, keywords, or authors.
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


# ── Main ──────────────────────────────────────────────────────

def main():
    config = load_config()

    print("Fetching papers by keyword (OpenAlex)...")
    keyword_papers = fetch_papers_by_keywords(config)
    print(f"  {len(keyword_papers)} unique papers from keyword searches")

    print("Fetching papers by tracked authors (OpenAlex)...")
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
