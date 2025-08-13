import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name")
    if not name:
        try:
            data = req.get_json()
            name = data.get("name") if isinstance(data, dict) else None
        except Exception:
            name = None
    body = {"message": f"Hello, {name or 'world'}!", "ok": True}
    import json
    return func.HttpResponse(
        body=json.dumps(body),
        mimetype="application/json",
        status_code=200,
    )
