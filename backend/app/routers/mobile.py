"""
mobile.py - lets a phone send a photo to the desktop app over the local network.

the desktop app cannot post a photo to /plants/{id}/photo before the plant
exists, so this router holds the photo in a staging slot instead. the flow is

    1. desktop calls POST /m/new and gets back a token
    2. desktop shows a qr code pointing at GET /m/{token}
    3. phone scans it and gets a small html upload page
    4. phone posts the image to POST /m/{token}
    5. desktop polls GET /m/{token}/status until it lands, then downloads it

tokens are single use and expire after 10 minutes. staged files live in
their own folder so they never mix with real plant photos.
"""

import os
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(prefix="/m", tags=["mobile"])

# staged photos are kept apart from the real plant uploads so nothing
# half finished can leak into a plant record
STAGING_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "staging"
)
os.makedirs(STAGING_DIR, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 mb
TOKEN_TTL_SECONDS = 10 * 60  # a qr code is only good for ten minutes

# token -> {"created": float, "path": str or None}
# this lives in memory on purpose. a staged photo only needs to survive the
# few seconds between the phone sending it and the desktop picking it up,
# so there is no reason to put it in the database
_sessions = {}


def _purge_expired():
    """drops old tokens and deletes whatever files they were holding"""
    now = time.time()
    for token in [t for t, s in _sessions.items()
                  if now - s["created"] > TOKEN_TTL_SECONDS]:
        session = _sessions.pop(token, None)
        if session and session.get("path") and os.path.exists(session["path"]):
            os.remove(session["path"])


def _get_session_or_404(token):
    _purge_expired()
    session = _sessions.get(token)
    if not session:
        raise HTTPException(status_code=404, detail="Upload link expired or invalid.")
    return session


@router.post("/new")
def create_upload_session():
    """desktop calls this to start a session and get a token for the qr code"""
    _purge_expired()
    token = uuid.uuid4().hex[:12]
    _sessions[token] = {"created": time.time(), "path": None}
    return {"token": token, "expires_in": TOKEN_TTL_SECONDS}





# mobile page

@router.get("/{token}", response_class=HTMLResponse)
def mobile_upload_page(token: str):
    """
    the page the phone lands on after scanning the qr code

    it is deliberately plain html with no build step and no javascript
    framework, because it has to load instantly over local wifi. capture
    is set so phones offer the camera as well as the photo library
    """
    _get_session_or_404(token)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Send a plant photo</title>
<style>
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
         background:#F6F5F0; color:#1F2A22; display:flex; align-items:center;
         justify-content:center; min-height:100vh; padding:24px; box-sizing:border-box; }}
  .card {{ background:#fff; border-radius:20px; padding:28px 22px; width:100%;
           max-width:380px; box-shadow:0 8px 30px rgba(0,0,0,.08); text-align:center; }}
  h1 {{ font-size:20px; margin:0 0 6px; }}
  p  {{ font-size:14px; color:#6B7A6E; margin:0 0 22px; }}
  label {{ display:block; background:#E8EFE6; border:2px dashed #2C4A33; border-radius:16px;
           padding:34px 16px; cursor:pointer; font-size:15px; color:#2C4A33; font-weight:600; }}
  input[type=file] {{ display:none; }}
  button {{ margin-top:18px; width:100%; padding:15px; border:0; border-radius:14px;
            background:#2C4A33; color:#fff; font-size:16px; font-weight:600; cursor:pointer; }}
  button:disabled {{ background:#9AA89C; }}
  #msg {{ margin-top:16px; font-size:14px; min-height:20px; }}
  img#preview {{ margin-top:16px; max-width:100%; border-radius:12px; display:none; }}
</style>
</head>
<body>
<div class="card">
  <h1>Send a plant photo</h1>
  <p>This goes straight to Sprout on your computer.</p>

  <label for="file" id="drop">Tap to take or choose a photo</label>
  <input id="file" type="file" accept="image/jpeg,image/png,image/webp" capture="environment">
  <img id="preview" alt="">

  <button id="send" disabled>Send photo</button>
  <div id="msg"></div>
</div>

<script>
  const fileInput = document.getElementById('file');
  const sendBtn   = document.getElementById('send');
  const msg       = document.getElementById('msg');
  const drop      = document.getElementById('drop');
  const preview   = document.getElementById('preview');

  fileInput.addEventListener('change', () => {{
    if (!fileInput.files.length) return;
    const f = fileInput.files[0];
    drop.textContent = f.name;
    preview.src = URL.createObjectURL(f);
    preview.style.display = 'block';
    sendBtn.disabled = false;
    msg.textContent = '';
  }});

  sendBtn.addEventListener('click', async () => {{
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    const data = new FormData();
    data.append('file', fileInput.files[0]);
    try {{
      const res = await fetch(window.location.pathname, {{ method:'POST', body:data }});
      if (res.ok) {{
        msg.style.color = '#2C4A33';
        msg.textContent = 'Sent. You can go back to your computer.';
        sendBtn.textContent = 'Sent';
      }} else {{
        const err = await res.json().catch(() => ({{}}));
        msg.style.color = '#B23B3B';
        msg.textContent = err.detail || 'Upload failed.';
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send photo';
      }}
    }} catch (e) {{
      msg.style.color = '#B23B3B';
      msg.textContent = 'Could not reach your computer.';
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send photo';
    }}
  }});
</script>
</body>
</html>"""




# 3 endpoints 

@router.post("/{token}")
def receive_mobile_photo(token: str, file: UploadFile = File(...)):
    """the phone posts the image here. same limits as the plant photo endpoint"""
    session = _get_session_or_404(token)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPEG, PNG, or WEBP.",
        )

    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB).")

    # if they send a second photo before the desktop grabs the first,
    # throw the old one away so we never leave a stray file behind
    if session.get("path") and os.path.exists(session["path"]):
        os.remove(session["path"])

    ext = CONTENT_TYPE_EXTENSIONS[file.content_type]
    filepath = os.path.join(STAGING_DIR, f"staged_{token}{ext}")
    with open(filepath, "wb") as f:
        f.write(contents)

    session["path"] = filepath
    return {"status": "received"}


@router.get("/{token}/status")
def upload_status(token: str):
    """desktop polls this while the qr code is on screen"""
    session = _get_session_or_404(token)
    return {"ready": session.get("path") is not None}


@router.get("/{token}/file")
def fetch_staged_photo(token: str):
    """
    desktop downloads the staged photo once status says it is ready

    the token stays alive afterwards so a retry still works. the file gets
    cleaned up when the token expires
    """
    session = _get_session_or_404(token)
    path = session.get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No photo uploaded yet.")
    return FileResponse(path)