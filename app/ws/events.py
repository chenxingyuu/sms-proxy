from cores.constant.socket import SioEvent, WsMessage
from cores.log import LOG
from cores.sio import sio


# 使用装饰器注册 connect 事件
@sio.on(SioEvent.CONNECT.value)
async def connect(sid, environ):
    LOG.info(f"客户端 {sid = } {environ = } 已连接")
    await sio.send("Connection success!", room=sid)


@sio.on(SioEvent.DISCONNECT.value)
async def disconnect(sid):
    LOG.info(f"客户端 {sid} 已断开连接")


@sio.on(SioEvent.ENTER_ROOM.value)
async def enter(sid, message: WsMessage):
    await sio.enter_room(sid=sid, room=message.room)
    LOG.info(f"enter room {sid = } {message.room = }")


@sio.on(SioEvent.LEAVE_ROOM.value)
async def leave(sid, message: WsMessage):
    await sio.leave_room(sid=sid, room=message.room)
    LOG.info(f"leave room {sid = } {message.room = }")


@sio.on(SioEvent.CLOSE_ROOM.value)
async def close(sid: str, message: WsMessage):
    await sio.close_room(sid=sid, room=message.room)
    LOG.info(f"客户端 {sid} 关闭房间 {message.room}")
