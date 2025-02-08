import asyncio
import json
import websockets
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCDataChannel, RTCSessionDescription

async def connect_websocket():
    uri = "ws://localhost:8080"
    return await websockets.connect(uri)

async def run():
    pc = RTCPeerConnection()
    ws = await connect_websocket()
    channel = pc.createDataChannel('fileChannel')

    @pc.on("icecandidate")
    async def on_icecandidate(event):
        if event.candidate:
            await ws.send(json.dumps({"candidate": event.candidate.__dict__}))

    @channel.on("open")
    async def on_channel_open():
        print("Data channel is open")
        # Send an image when the channel is open
        with open('/Users/daniellawton/Documents/FYP/Prototype/pic_test/norse.png', 'rb') as file:
            image_data = file.read()
            channel.send(image_data)
            print("Image has been sent")

    # Create offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await ws.send(json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))

    # Listen for answer
    try:
        async for message in ws:
            data = json.loads(message)
            if data['type'] == 'answer':
                await pc.setRemoteDescription(RTCSessionDescription(sdp=data['sdp'], type=data['type']))
            elif data['type'] == 'candidate' and data['candidate']:
                candidate = RTCIceCandidate(**data['candidate'])
                await pc.addIceCandidate(candidate)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await ws.close()
        await pc.close()

asyncio.run(run())
