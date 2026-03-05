import modal

app = modal.App("hello-world")


@app.function()
def greet(name: str) -> str:
    return f"Hello, {name}! Running on Modal."


@app.local_entrypoint()
def main():
    result = greet.remote("Prince")
    print(result)
