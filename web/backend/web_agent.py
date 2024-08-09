import asyncio
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup


async def main(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url)
        await page.wait_for_load_state("domcontentloaded")

        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')

        with open("output.txt", "w") as file:
            file.write(soup.prettify())


asyncio.run(main('https://github.com'))