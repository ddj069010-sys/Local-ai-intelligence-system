import logging
import asyncio
import os
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class DynamicScraper:
    def __init__(self):
        self.browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ]
    async def fetch_rich_context(self, url: str, tmp_dir: str) -> Optional[Dict[str, Any]]:
        """Launches Playwright to extract HTML, Screenshots, and Layout intelligence."""
        try:
            logger.info(f"🕸️ [DYNAMIC SCRAPER] Launching Rich Visual Scraper: {url}")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=self.browser_args)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                
                # 1. Navigate
                await page.goto(url, wait_until="networkidle", timeout=20000)
                
                # 2. 🖱️ INTERACTION: Handle common overlays
                try:
                    # Click common 'Accept' buttons to clear the view
                    for text in ["Accept", "Agree", "Allow", "Got it"]:
                        btn = page.get_by_role("button", name=text, exact=False)
                        if await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(0.5)
                except: pass
                
                # 3. 📸 SCREENSHOT: For AI-Vision analysis
                screenshot_path = os.path.join(tmp_dir, "page_snapshot.png")
                await page.screenshot(path=screenshot_path, full_page=False)
                
                # 4. Extract Data
                html_content = await page.content()
                
                # 5. Visual Layout Logic (Brief)
                # Identify main CTA buttons
                cta_buttons = await page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, a.btn, .button'));
                    return btns.filter(b => b.innerText.length > 2 && b.offsetHeight > 0).map(b => b.innerText).slice(0, 5);
                }""")
                
                await browser.close()
                return {
                    "html": html_content,
                    "screenshot_path": screenshot_path,
                    "cta": cta_buttons
                }
                
        except Exception as e:
            logger.error(f"❌ [DYNAMIC SCRAPER] Failed fetch {url}: {e}")
            return None

dynamic_scraper = DynamicScraper()

dynamic_scraper = DynamicScraper()
