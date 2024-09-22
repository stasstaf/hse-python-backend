import json
from math import factorial
from urllib.parse import parse_qs


async def app(scope, receive, send):
    assert scope['type'] == 'http'

    method = scope['method']
    path = scope['path']
    query_string = scope['query_string'].decode()

    if path == '/factorial' and method == 'GET':
        query_params = parse_qs(query_string)
        if 'n' not in query_params:
            await send_response(send, 422, {"error": "Parameter 'n' is required and must be an integer."})
            return
        try:
            n = int(query_params['n'][0])
        except ValueError:
            await send_response(send, 422, {"error": "Parameter 'n' is required and must be an integer."})
            return
        if n < 0:
            await send_response(send, 400, {"error": "Parameter 'n' must be a non-negative integer."})
            return
        result = factorial(n)
        await send_response(send, 200, {"result": result})

    elif path.startswith('/fibonacci/') and method == 'GET':
        try:
            n = int(path[len('/fibonacci/'):])
        except ValueError:
            await send_response(send, 422, {"error": "Path parameter 'n' must be a valid integer."})
            return
        if n < 0:
            await send_response(send, 400, {"error": "Path parameter 'n' must be a non-negative integer."})
            return
        result = fibonacci(n)
        await send_response(send, 200, {"result": result})

    elif path == '/mean' and method == 'GET':
        request = await receive()
        body = request['body'].decode('utf-8')
        try:
            data = json.loads(body)
            if not isinstance(data, list) or not all(isinstance(i, (int, float)) for i in data):
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
            await send_response(send, 422, {"error": "Request body must be a non-empty array of numbers."})
            return
        if not data:
            await send_response(send, 400, {"error": "Array must not be empty."})
            return
        result = sum(data) / len(data)
        await send_response(send, 200, {"result": result})

    else:
        await send_response(send, 404, {"error": "Not Found"})


async def send_response(send, status, body):
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [(b'content-type', b'application/json')],
    })
    await send({
        'type': 'http.response.body',
        'body': json.dumps(body).encode(),
    })


def fibonacci(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
