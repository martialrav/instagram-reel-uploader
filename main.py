# instagram_reel_uploader.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
import json

app = FastAPI()

COOKIES_FILE = "storage_state.json"
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")
UPLOAD_FOLDER = "/mnt/data/reel_queue"  # Mount your drive here

class LoginRequest(BaseModel):
    username: str
    password: str

class PostRequest(BaseModel):
    video: str
    caption: str

@app.post("/login")
async def login(data: LoginRequest):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.instagram.com/accounts/login/")
        await page.wait_for_selector("input[name='username']")

        await page.fill("input[name='username']", data.username)
        await page.fill("input[name='password']", data.password)
        await page.click("button[type='submit']")

        await page.wait_for_timeout(7000)  # wait for redirect/login
        await context.storage_state(path=COOKIES_FILE)
        await browser.close()
        return {"status": "logged in"}

@app.post("/post")
async def upload_video(data: PostRequest):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=COOKIES_FILE)
        page = await context.new_page()

        await page.goto("https://www.instagram.com/")
        await page.wait_for_timeout(3000)

        # Click the Create button
        await page.click("[aria-label='New post']")
        await page.wait_for_selector("input[type='file']")
        await page.set_input_files("input[type='file']", data.video)

        # Wait and proceed through steps
        await page.wait_for_timeout(3000)
        await page.click("text=Next")
        await page.wait_for_timeout(2000)
        await page.click("text=Next")
        await page.fill("textarea", data.caption)
        await page.click("text=Share")

        await page.wait_for_timeout(10000)
        await browser.close()

        return {"status": "posted", "video": data.video}

@app.get("/")
def root():
    return {"status": "ready"}
