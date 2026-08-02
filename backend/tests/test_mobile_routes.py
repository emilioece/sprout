import os

from app.routers import mobile


def test_mobile_upload_uses_extension_from_content_type(client):
    token = client.post("/m/new").json()["token"]

    response = client.post(
        f"/m/{token}",
        files={"file": ("../../weird-name.txt", b"image-bytes", "image/png")},
    )

    assert response.status_code == 200

    staged_path = mobile._sessions[token]["path"]
    assert staged_path == os.path.join(mobile.STAGING_DIR, f"staged_{token}.png")

    os.remove(staged_path)
    mobile._sessions.pop(token, None)
