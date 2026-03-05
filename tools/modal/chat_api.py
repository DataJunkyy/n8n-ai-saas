import modal
from fastapi import Request
from fastapi.responses import JSONResponse

image = modal.Image.debian_slim().pip_install("fastapi[standard]")
app = modal.App("chat-demo", image=image)


@app.function()
@modal.fastapi_endpoint(method="POST")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    return JSONResponse({
        "output": f"Echo from Modal: {message}",
        "source": "modal-serverless",
    })


@app.function()
@modal.fastapi_endpoint(method="GET")
async def health():
    return JSONResponse({"status": "ok", "platform": "modal"})
