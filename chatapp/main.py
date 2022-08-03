from fastapi import FastAPI, WebSocket, Request, Cookie, Depends, Query, status, WebSocketDisconnect
# from fastapi.responses import HTMLResponse
from typing import Union, List
from fastapi.templating import Jinja2Templates
import json


app = FastAPI()

templates = Jinja2Templates(directory="templates")

#------------------------------------------------------------------------------------------

@app.get("/")
async def get(request: Request,):
    return templates.TemplateResponse("test_ws.html",{"request": request}) 


@app.websocket("/ws")
async def websocket_endpoint(websocket : WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f'you just texted: {data}')


#----------------------------------------------------------------------------------
@app.get("/token")
async def get_token(request: Request):
    return templates.TemplateResponse("token_cookie.html",{"request": request}) 


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Union[str, None] = Cookie(default=None),
    token: Union[str, None] = Query(default=None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/items/{item_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    item_id: str,
    q: Union[int, None] = None,
    cookie_or_token: str = Depends(get_cookie_or_token),
):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(
            f"Session cookie or query token value is: {cookie_or_token}"
        )
        if q is not None:
            await websocket.send_text(f"Query parameter q is: {q}")
        await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")



#----------------------------------------------------------


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#         self.client_websocket = {}

#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#         self.client_websocket[str(uuid.uuid4())]=websocket

#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)

#     async def send_personal_message(self, message: str, websocket: WebSocket,client_id):
#         await websocket.send_text(message)

#     async def broadcast(self, message: str):
#         for connection in self.active_connections:
#             await connection.send_text(message)


# manager = ConnectionManager()

# @app.get("/clients")
# async def multi_client(request : Request):
#     return templates.TemplateResponse("handling_exception.html",{"request": request}) 


# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket,client_id)
#     try:
#         while True:
#             data = await websocket.receive_text()

#             await manager.send_personal_message(f"You wrote: {data}", websocket)
#             # await manager.broadcast(f"Client #{client_id} says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} left the chat")




##--------------------------------------------------------------------------------


class validationError(Exception):
    pass

connections = {}

async def chat(data, websocket):
    user_number = data['user_number']
    connections[user_number] = websocket
    websocket_list = [websocket]
    receiver_number = data['receiver_number']
    get_receiver = connections.get(receiver_number)
    if get_receiver:
        websocket_list.append(get_receiver)
    for websocket in websocket_list:
        websocket.send_text(json.dumps(data))
    print(connections,'conne....................')
        

async def validate(data):
    try:
        if data['my_number'] and data['receiver_number'] and data['message'] != "":
            return True
        else:
            raise validationError("All fileds are required")
    except validationError:
        print(validationError)


@app.get("/chat")
async def one_to_one_chat(request : Request):
    return templates.TemplateResponse("one_to_one.html",{"request": request}) 


@app.websocket("/ws")
async def websocket_endpoint(websocket : WebSocket):
    await websocket.accept()
    while True:
        try:
            data = json.loads(await websocket.receive_text())
            if validate(data):
                await chat(data, websocket)
        except WebSocketDisconnect as disconnect:
            websocket.close()
            print(str(disconnect))

            