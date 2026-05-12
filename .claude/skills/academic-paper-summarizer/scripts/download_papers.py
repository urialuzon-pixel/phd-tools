"""
download_papers.py
------------------
General-purpose academic paper downloader.

Input:  list of paper titles (or dicts with title/doi)
Output: PDF files saved to output_dir

Pipeline per paper:
  1. Resolve DOI via CrossRef
  2. Find open-access PDF via Semantic Scholar → Unpaywall → OpenAlex
  3. Download:
       a. Simple HTTP (fast, no browser)
       b. Playwright + stealth (Cloudflare-protected sites)
  4. Log result

Usage:
    python scripts/download_papers.py --input "pdfs/list of papers.docx" --output pdfs/
    python scripts/download_papers.py --titles "Title one" "Title two" --output pdfs/
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import time

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import httpx
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

_stealth = Stealth()

async def apply_stealth(page):
    await _stealth.apply_stealth_async(page)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Paper:
    title: str
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    filename: Optional[str] = None
    status: str = "pending"   # pending | downloaded | failed | no_pdf
    note: str = ""


# ---------------------------------------------------------------------------
# Step 1 – DOI resolution via CrossRef
# ---------------------------------------------------------------------------

async def resolve_doi(client: httpx.AsyncClient, title: str) -> Optional[str]:
    url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=1&select=DOI,title"
    try:
        r = await client.get(url, timeout=15)
        items = r.json().get("message", {}).get("items", [])
        if items:
            return items[0].get("DOI")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Step 2 – PDF URL discovery
# ---------------------------------------------------------------------------

async def find_pdf_semantic_scholar(client: httpx.AsyncClient, title: str) -> Optional[str]:
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={quote_plus(title)}&fields=openAccessPdf&limit=1"
    try:
        r = await client.get(url, timeout=15)
        data = r.json().get("data", [])
        if data and data[0].get("openAccessPdf"):
            return data[0]["openAccessPdf"].get("url")
    except Exception:
        pass
    return None


async def find_pdf_unpaywall(client: httpx.AsyncClient, doi: str, email: str) -> Optional[str]:
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        r = await client.get(url, timeout=15)
        loc = r.json().get("best_oa_location") or {}
        return loc.get("url_for_pdf")
    except Exception:
        pass
    return None


async def find_pdf_openalex(client: httpx.AsyncClient, doi: str) -> Optional[str]:
    url = f"https://api.openalex.org/works/doi:{doi}?select=open_access"
    try:
        r = await client.get(url, timeout=15)
        oa = r.json().get("open_access", {})
        return oa.get("oa_url")
    except Exception:
        pass
    return None


async def find_pdf_google_scholar(page, title: str) -> Optional[str]:
    """Scrape Google Scholar for a [PDF] link using a stealth browser page."""
    try:
        q = quote_plus(title)
        await page.goto(f"https://scholar.google.com/scholar?q={q}", timeout=20000)
        await page.wait_for_timeout(1500)
        # Check for CAPTCHA
        if "captcha" in (await page.content()).lower():
            return None
        result = await page.evaluate("""
            () => {
                for (const el of document.querySelectorAll('.gs_r.gs_or')) {
                    const a = el.querySelector('.gs_or_ggsm a, a[href*=".pdf"]');
                    if (a) return a.href;
                }
                return null;
            }
        """)
        return result
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Step 3 – Download
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
    "Referer": "https://scholar.google.com/",
}


async def simple_download(client: httpx.AsyncClient, url: str, dest: Path) -> bool:
    """Direct HTTP download. Returns True on success."""
    try:
        async with client.stream("GET", url, headers=HEADERS, timeout=60, follow_redirects=True) as r:
            if r.status_code != 200:
                return False
            content = await r.aread()
            if len(content) < 5000 or not content.startswith(b"%PDF"):
                return False
            dest.write_bytes(content)
            return True
    except Exception:
        return False


def _normalize_pdf_url(url: str) -> str:
    """Fix known bad URL patterns from Unpaywall/OpenAlex."""
    # PMC article page (both www.ncbi and pmc.ncbi) → PDF endpoint
    m = re.search(r'ncbi\.nlm\.nih\.gov/pmc/articles/(PMC)?(\d+)', url)
    if m:
        pmc_id = f"PMC{m.group(2)}"
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
    # DOI redirect for SSRN → use Delivery URL
    if "doi.org/10.2139/ssrn." in url:
        ssrn_id = url.split("ssrn.")[-1].strip()
        return f"https://papers.ssrn.com/sol3/Delivery.cfm?abstractid={ssrn_id}"
    # Wiley: /doi/full/ or /doi/abs/ → /doi/pdf/ (viewer, not direct PDF)
    url = re.sub(r'/doi/(full|abs)/', '/doi/pdf/', url)
    return url


def _is_wiley_url(url: str) -> bool:
    return "onlinelibrary.wiley.com" in url or "agupubs.onlinelibrary" in url


async def _wait_for_cloudflare(page, max_wait_s: int = 30) -> bool:
    """
    Wait for Cloudflare to clear (auto or via user interaction).
    Returns True if page is now accessible.
    """
    for _ in range(max_wait_s):
        content = await page.content()
        blocked = any(k in content.lower() for k in [
            "security verification", "verifying", "checking your browser",
            "enable javascript", "ddos-guard"
        ])
        if not blocked:
            return True
        await asyncio.sleep(1)
    return False


async def stealth_download(page, url: str, dest: Path) -> bool:
    """
    Fetch PDF via persistent stealth browser (bypasses Cloudflare).
    - Navigates to URL, waits for Cloudflare to clear (auto or user-solved)
    - Fetches PDF bytes via browser JS, triggers download
    - Moves downloaded file to dest
    """
    try:
        url = _normalize_pdf_url(url)
        await page.goto(url, timeout=40000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Handle Cloudflare — wait up to 30s (user can solve challenge manually)
        content = await page.content()
        is_blocked = any(k in content.lower() for k in [
            "security verification", "verifying", "checking your browser",
            "enable javascript", "ddos-guard"
        ])
        if is_blocked:
            print("    [browser] Cloudflare detected — waiting up to 30s...")
            cleared = await _wait_for_cloudflare(page, max_wait_s=30)
            if not cleared:
                return False
            await page.wait_for_timeout(1000)

        # --- Wiley: PDF is inside an iframe, navigate into it ---
        if _is_wiley_url(url):
            iframe_src = await page.evaluate("""
                () => {
                    for (const f of document.querySelectorAll('iframe')) {
                        if (f.src && f.src.includes('pdfdirect')) return f.src;
                    }
                    return null;
                }
            """)
            if iframe_src:
                # Navigate directly to the embedded PDF URL (same session = cookies carry over)
                await page.goto(iframe_src, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                cleared = await _wait_for_cloudflare(page, max_wait_s=20)
                if not cleared:
                    return False
                url = iframe_src  # fall through to fetch below

        # Fetch PDF bytes via browser JS (uses session cookies — same-origin fetch)
        dl_filename = "__paper_dl__.pdf"
        size = await page.evaluate(f"""
            async () => {{
                const r = await fetch(window.location.href, {{credentials: 'include'}});
                const buf = await r.arrayBuffer();
                const bytes = new Uint8Array(buf);
                if (bytes[0] !== 37) return 0;   // not %PDF
                const blob = new Blob([bytes], {{type: 'application/pdf'}});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = {json.dumps(dl_filename)};
                document.body.appendChild(a);
                a.click();
                return bytes.byteLength;
            }}
        """)
        if not size:
            return False

        # Wait for file to land in Downloads
        dl_path = Path.home() / "Downloads" / dl_filename
        for _ in range(40):
            await asyncio.sleep(0.5)
            if dl_path.exists() and dl_path.stat().st_size > 5000:
                dl_path.rename(dest)
                return True
        return False
    except Exception as e:
        print(f"    [stealth] error: {e}")
        return False


# ---------------------------------------------------------------------------
# Title → safe filename
# ---------------------------------------------------------------------------

def safe_filename(title: str, doi: Optional[str] = None) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", title)
    name = re.sub(r'\s+', "_", name.strip())
    return name[:80] + ".pdf"


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_docx(path: Path) -> list[str]:
    """Extract text from a .docx file and split into paper titles."""
    import zipfile
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode()
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        text = "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
        text = text.strip()
        if text:
            paragraphs.append(text)
    return paragraphs


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def process_paper(
    paper: Paper,
    client: httpx.AsyncClient,
    scholar_page,
    stealth_page,
    output_dir: Path,
    email: str,
    delay: float,
) -> None:
    print(f"\n{'-'*60}")
    print(f"  {paper.title[:70]}")

    dest = output_dir / (paper.filename or safe_filename(paper.title, paper.doi))

    if dest.exists():
        paper.status = "downloaded"
        paper.note = "already exists"
        print(f"  → already exists, skipping")
        return

    # Step 1: resolve DOI
    if not paper.doi:
        paper.doi = await resolve_doi(client, paper.title)
        print(f"  DOI: {paper.doi or 'not found'}")
    await asyncio.sleep(delay)

    # Step 2: find PDF URL
    if not paper.pdf_url:
        paper.pdf_url = await find_pdf_semantic_scholar(client, paper.title)
        await asyncio.sleep(delay)

    if not paper.pdf_url and paper.doi:
        paper.pdf_url = await find_pdf_unpaywall(client, paper.doi, email)
        await asyncio.sleep(delay)

    if not paper.pdf_url and paper.doi:
        paper.pdf_url = await find_pdf_openalex(client, paper.doi)
        await asyncio.sleep(delay)

    if not paper.pdf_url:
        paper.pdf_url = await find_pdf_google_scholar(scholar_page, paper.title)

    if not paper.pdf_url:
        paper.status = "no_pdf"
        paper.note = "no open-access PDF found"
        print(f"  → no open-access PDF found")
        return

    print(f"  PDF URL: {paper.pdf_url[:80]}")

    # Step 3a: simple download
    ok = await simple_download(client, paper.pdf_url, dest)
    if ok:
        paper.status = "downloaded"
        paper.note = f"simple HTTP ({dest.stat().st_size // 1024}KB)"
        print(f"  ✓ downloaded ({dest.stat().st_size // 1024}KB)")
        return

    # Step 3b: stealth browser download
    print(f"  simple download failed → trying stealth browser...")
    ok = await stealth_download(stealth_page, paper.pdf_url, dest)
    if ok:
        paper.status = "downloaded"
        paper.note = f"stealth browser ({dest.stat().st_size // 1024}KB)"
        print(f"  ✓ downloaded via stealth ({dest.stat().st_size // 1024}KB)")
        return

    paper.status = "failed"
    paper.note = "blocked (Cloudflare/paywall)"
    print(f"  ✗ failed — blocked or paywall")


async def run(titles: list[str], output_dir: Path, email: str, delay: float, profile_dir: Path):
    papers = [Paper(title=t) for t in titles]
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with async_playwright() as pw:
            # Scholar page: stealth, no persistent profile needed
            scholar_browser = await pw.chromium.launch(headless=True)
            scholar_context = await scholar_browser.new_context()
            scholar_page = await scholar_context.new_page()
            await apply_stealth(scholar_page)

            # Stealth download page: persistent profile (stores cookies/session)
            stealth_context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=False,  # visible — helps pass Cloudflare
                args=["--disable-blink-features=AutomationControlled"],
            )
            stealth_page = await stealth_context.new_page()
            await apply_stealth(stealth_page)

            for paper in papers:
                await process_paper(
                    paper, client, scholar_page, stealth_page,
                    output_dir, email, delay
                )
                await asyncio.sleep(delay)

            await scholar_browser.close()
            await stealth_context.close()

    # Summary
    print(f"\n{'='*60}", flush=True)
    downloaded = [p for p in papers if p.status == "downloaded"]
    failed     = [p for p in papers if p.status == "failed"]
    no_pdf     = [p for p in papers if p.status == "no_pdf"]

    print(f"Downloaded : {len(downloaded)}/{len(papers)}")
    print(f"Failed     : {len(failed)}")
    print(f"No PDF     : {len(no_pdf)}")

    if failed or no_pdf:
        print("\nManual download needed:")
        for p in failed + no_pdf:
            print(f"  [{p.status}] {p.title[:60]} — {p.note}")

    # Save log
    log_path = output_dir / "download_log.json"
    log = [{"title": p.title, "doi": p.doi, "pdf_url": p.pdf_url,
            "status": p.status, "note": p.note} for p in papers]
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False))
    print(f"\nLog saved: {log_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download academic papers as PDF")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", help="Path to .docx or .txt file with paper titles")
    src.add_argument("--titles", nargs="+", help="Paper titles directly on command line")
    parser.add_argument("--output", default="pdfs", help="Output directory (default: pdfs/)")
    parser.add_argument("--email", default="urialuzon@gmail.com", help="Email for Unpaywall API")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between API calls")
    parser.add_argument("--profile", default="browser_profile",
                        help="Directory for persistent browser profile (stores Cloudflare cookies)")
    args = parser.parse_args()

    if args.input:
        p = Path(args.input)
        if p.suffix == ".docx":
            titles = parse_docx(p)
        else:
            titles = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        titles = args.titles

    print(f"Papers to download: {len(titles)}")
    asyncio.run(run(
        titles=titles,
        output_dir=Path(args.output),
        email=args.email,
        delay=args.delay,
        profile_dir=Path(args.profile),
    ))


if __name__ == "__main__":
    main()
