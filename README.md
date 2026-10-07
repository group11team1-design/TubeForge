# TubeForge — Public Website

TubeForge has two parts:

- **GitHub Pages** → public website interface
- **Flask backend** → yt-dlp + FFmpeg download engine

## Publish the website

1. Create a GitHub repository.
2. Upload/push this project to the `main` branch.
3. Go to **Settings → Pages**.
4. Choose **GitHub Actions** as the source.
5. The included workflow deploys `index.html`, `static/`, and the other frontend files.

## Connect the downloader

GitHub Pages cannot run Flask, Python, yt-dlp, or FFmpeg.

Deploy `app.py` to a Python-capable host such as Render, then edit `config.js`:

```js
window.TUBEFORGE_API = "https://YOUR-BACKEND-URL";
```

Commit and push again.

Then the public GitHub Pages site sends its `/api/*` requests to your Flask backend.

## Backend

The repository includes:

- `app.py`
- `requirements.txt`
- `render.yaml`

Render start command:

```text
gunicorn app:app
```

## Local development

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000`.

## Important

Only download content you are authorized to download. Do not bypass DRM, private-content restrictions, access controls, or other platform restrictions. Follow applicable law and the source platform's terms.
