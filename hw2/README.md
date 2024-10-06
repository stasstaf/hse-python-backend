# ДЗ 2
Доп задание:
```bash
uvicorn lecture_2.hw.shop_api.websocket:app --host 127.0.0.1 --port 8001 --reload
```
Чтобы подключиться к чату:
```bash
wscat -c ws://127.0.0.1:8001/chat/room1
```
