import asyncio
import json
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate

async def connect_websocket():
    uri = "ws://localhost:8080"
    return await websockets.connect(uri)

async def run():
    pc = RTCPeerConnection()
    ws = await connect_websocket()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on('message')
        def on_message(message):
            print("Received message:", message)
            with open('received_image.jpg', 'wb') as file:
                file.write(message)

    # Listen for offer
    async for message in ws:
        data = json.loads(message)
        if data['type'] == 'offer':
            await pc.setRemoteDescription(RTCSessionDescription(sdp=data['sdp'], type=data['type']))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await ws.send(json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))
        elif data['type'] == 'candidate' and data['candidate']:
            candidate = RTCIceCandidate(**data['candidate'])
            await pc.addIceCandidate(candidate)

    await asyncio.sleep(30)  # Keep alive
    await pc.close()

asyncio.run(run())
