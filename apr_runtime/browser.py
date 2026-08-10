from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Protocol

from .sources import SourceUnavailable


@dataclass(frozen=True)
class BrowserSnapshot:
    url: str
    title: str
    aria_snapshot: str
    aria_digest: str
    dom_digest: str
    dom_element_count: int
    active_element: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class BrowserSource(Protocol):
    def page(self):
        """Return the currently selected Playwright Page."""
        return self._page()

    def snapshot(self) -> BrowserSnapshot: ...


class PlaywrightCDPBrowserSource:
    """
    Attach to an existing Chromium browser over CDP.

    The source intentionally reads bounded native structure:
      - URL / title
      - bounded ARIA snapshot
      - bounded DOM structural sample
      - active element metadata

    It does not screenshot the page and does not dump unlimited page HTML.
    """

    def __init__(
        self,
        endpoint_url: str = "http://127.0.0.1:9222",
        *,
        page_index: int = -1,
        aria_depth: int = 5,
        max_dom_elements: int = 500,
        max_text_per_element: int = 80,
        timeout_ms: float = 5000,
        no_defaults: bool = True,
    ) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise SourceUnavailable(
                "playwright is not installed. Install browser extras with "
                "pip install -e '.[browser]'"
            ) from exc

        self._sync_playwright = sync_playwright
        self.endpoint_url = endpoint_url
        self.page_index = page_index
        self.aria_depth = aria_depth
        self.max_dom_elements = max_dom_elements
        self.max_text_per_element = max_text_per_element
        self.timeout_ms = timeout_ms
        self.no_defaults = no_defaults

        self._pw = None
        self._browser = None

    def _ensure_browser(self):
        if self._browser is not None:
            return self._browser

        self._pw = self._sync_playwright().start()
        kwargs = {"timeout": self.timeout_ms}
        if self.no_defaults:
            kwargs["no_defaults"] = True

        try:
            self._browser = self._pw.chromium.connect_over_cdp(
                self.endpoint_url,
                **kwargs,
            )
        except TypeError:
            # Compatibility with older Playwright versions that do not yet
            # expose no_defaults.
            kwargs.pop("no_defaults", None)
            self._browser = self._pw.chromium.connect_over_cdp(
                self.endpoint_url,
                **kwargs,
            )

        return self._browser

    def _page(self):
        browser = self._ensure_browser()
        pages = [page for context in browser.contexts for page in context.pages]
        if not pages:
            raise SourceUnavailable("Connected Chromium instance has no pages.")
        try:
            return pages[self.page_index]
        except IndexError as exc:
            raise SourceUnavailable(
                f"page_index={self.page_index} unavailable; found {len(pages)} page(s)."
            ) from exc

    @staticmethod
    def _digest(value: Any) -> str:
        if isinstance(value, str):
            raw = value.encode("utf-8", "replace")
        else:
            raw = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        return sha256(raw).hexdigest()

    def page(self):
        """Return the currently selected Playwright Page."""
        return self._page()

    def snapshot(self) -> BrowserSnapshot:
        page = self._page()
        title = page.title()
        url = page.url

        body = page.locator("body")
        try:
            aria = body.aria_snapshot(
                mode="ai",
                depth=self.aria_depth,
                timeout=self.timeout_ms,
            )
        except TypeError:
            # Older Playwright releases support aria_snapshot() but not
            # AI/depth parameters.
            aria = body.aria_snapshot(timeout=self.timeout_ms)

        dom_sample = page.evaluate(
            """
            ([maxElements, maxText]) => {
              const nodes = Array.from(document.querySelectorAll('body *'))
                .slice(0, maxElements);
              return nodes.map((el) => ({
                tag: el.tagName,
                id: el.id || '',
                role: el.getAttribute('role') || '',
                aria: el.getAttribute('aria-label') || '',
                name: el.getAttribute('name') || '',
                type: el.getAttribute('type') || '',
                text: (el.innerText || el.textContent || '')
                  .trim()
                  .replace(/\\s+/g, ' ')
                  .slice(0, maxText)
              }));
            }
            """,
            [self.max_dom_elements, self.max_text_per_element],
        )

        active = page.evaluate(
            """
            () => {
              const el = document.activeElement;
              if (!el) return {};
              return {
                tag: el.tagName || '',
                id: el.id || '',
                role: el.getAttribute?.('role') || '',
                aria: el.getAttribute?.('aria-label') || '',
                name: el.getAttribute?.('name') || '',
                type: el.getAttribute?.('type') || ''
              };
            }
            """
        )

        return BrowserSnapshot(
            url=url,
            title=title,
            aria_snapshot=aria,
            aria_digest=self._digest(aria),
            dom_digest=self._digest(dom_sample),
            dom_element_count=len(dom_sample),
            active_element=active or {},
        )

    def close(self) -> None:
        # Do NOT call browser.close() here: this source attaches to an existing
        # user-managed Chromium instance over CDP. Closing the Browser object
        # may terminate that browser. We only tear down Playwright's client
        # connection/driver.
        self._browser = None
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None
