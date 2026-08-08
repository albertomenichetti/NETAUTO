from __future__ import annotations

import socket
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
import uvicorn
from fastapi import FastAPI


def _allocate_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


@asynccontextmanager
async def serve_app(app: FastAPI) -> AsyncIterator[httpx2.AsyncClient]:
    port = _allocate_port()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(200):
        if server.started:
            break
        time.sleep(0.01)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("Uvicorn test server did not start.")

    try:
        async with httpx2.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
        ) as client:
            yield client
    finally:
        server.should_exit = True
        thread.join(timeout=5)
