import sys
import types
import unittest
from unittest.mock import patch

from scripts.download_statistics import playwright_factory


class PlaywrightImportRegressionTests(unittest.TestCase):
    def test_playwright_factory_imports_async_api_lazily(self):
        sentinel = object()
        playwright_module = types.ModuleType("playwright")
        async_api_module = types.ModuleType("playwright.async_api")
        async_api_module.async_playwright = sentinel
        with patch.dict(sys.modules, {
            "playwright": playwright_module,
            "playwright.async_api": async_api_module,
        }):
            self.assertIs(playwright_factory(), sentinel)


if __name__ == "__main__":
    unittest.main()
