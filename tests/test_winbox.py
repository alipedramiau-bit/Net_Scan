from fastapi.testclient import TestClient
from backend.main import app
from backend import auth

client = TestClient(app)
# The API is protected by the admin session middleware; authenticate once.
client.cookies.set(auth.COOKIE_NAME, auth.create_token(auth.ADMIN_USER))


def test_winbox_list_endpoint():
    res = client.get("/api/winbox/list")
    assert res.status_code == 200
    d = res.json()
    assert "items" in d and isinstance(d["items"], list)
    assert "tools_dir" in d


def test_winbox_invalid_ip_rejected():
    res = client.post("/devices/999.999.1.1/winbox")
    assert res.status_code == 400


def test_winbox_not_found_returns_404(monkeypatch):
    monkeypatch.setattr("backend.main._resolve_winbox_exe", lambda _id=None: None)
    res = client.post("/devices/172.18.1.12/winbox")
    assert res.status_code == 404
    assert "Winbox" in res.json()["detail"]


def test_winbox_launch_with_mock_exe(monkeypatch):
    called = []

    def fake_popen(cmd, **kwargs):
        called.append(cmd)
        return None

    monkeypatch.setattr(
        "backend.main._resolve_winbox_exe",
        lambda _id=None: "C:\\Program Files\\WinBox\\winbox64.exe",
    )
    monkeypatch.setattr("backend.main.subprocess.Popen", fake_popen)

    res = client.post("/devices/192.168.88.1/winbox")
    assert res.status_code == 200
    d = res.json()
    assert d["ok"] is True
    assert d["ip"] == "192.168.88.1"
    assert called == [["C:\\Program Files\\WinBox\\winbox64.exe", "192.168.88.1"]]


def test_winbox_wine_launch(monkeypatch):
    called = []

    def fake_popen(cmd, **kwargs):
        called.append(cmd)
        return None

    monkeypatch.setattr("backend.main._resolve_winbox_exe", lambda _id=None: "/usr/bin/wine")
    monkeypatch.setattr("backend.main.subprocess.Popen", fake_popen)

    res = client.post("/devices/10.0.0.5/winbox")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert called == [["/usr/bin/wine", "winbox.exe", "10.0.0.5"]]
