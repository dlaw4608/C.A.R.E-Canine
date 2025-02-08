import asyncio
import json
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaPlayer

async def connect_websocket():
    uri = "ws://localhost:8080"
    return await websockets.connect(uri)

def create_player():
    return MediaPlayer('FaceTime HD Camera', format='avfoundation', options={'framerate': '30', 'video_size': '1280x720'})

async def run():
    pc = RTCPeerConnection()
    ws = await connect_websocket()
    
    player = create_player()
    if player.video:
        pc.addTrack(player.video)  # Directly add the video track without iterating

    @pc.on("icecandidate")
    async def on_icecandidate(event):
        if event.candidate:
            await ws.send(json.dumps({"candidate": event.candidate.__dict__}))

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await ws.send(json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))

    async for message in ws:
        data = json.loads(message)
        if data['type'] == 'answer':
            await pc.setRemoteDescription(RTCSessionDescription(sdp=data['sdp'], type=data['type']))
        elif data['type'] == 'candidate' and data['candidate']:
            candidate = RTCIceCandidate(**data['candidate'])
            await pc.addIceCandidate(candidate)

    # Keep the connection active until manually terminated or timed out
    await asyncio.sleep(3600)
    await pc.close()
    await ws.close()

asyncio.run(run())
