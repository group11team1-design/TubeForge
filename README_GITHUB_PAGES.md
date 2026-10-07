# TubeForge — GitHub Pages Website

TubeForge is a polished web frontend for the TubeForge downloader.

## Publish the website on GitHub Pages

1. Create a GitHub repository, for example `TubeForge`.
2. Upload this project's files to the repository.
3. Push to the `main` branch.
4. In GitHub, open **Settings → Pages**.
5. Set the source to **GitHub Actions**.
6. Push a change or run the **Deploy TubeForge to GitHub Pages** workflow.
7. GitHub will give you a public website URL.

## Important: GitHub Pages is frontend-only

GitHub Pages serves HTML/CSS/JavaScript. It cannot run Flask, yt-dlp, or FFmpeg.

Therefore the public website needs a backend API for the actual download operations.

### Architecture

Browser / GitHub Pages
→ TubeForge Flask API
→ yt-dlp
→ source platform
→ FFmpeg
→ backend download file

Deploy the existing Flask `app.py` to a Python-capable server and put its HTTPS URL in:

`config.js`

Example:

```js
window.TUBEFORGE_API = "https://your-backend.example.com";
```

Do not put passwords, API keys, cookies, or private credentials in `config.js`.

## Local development

The Flask project can still be run locally using the instructions in the main README.

## Usage policy

Use the downloader only for content you are authorized to download and follow the source platform's terms and applicable law.
