import json
import cv2
import asyncio
import logging
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from aiohttp import web

class VideoCamera(MediaStreamTrack):
    """
    A video stream track that captures video from the webcam using OpenCV.
    """
    kind = "video"

    def __init__(self, device='FaceTime HD Camera'):
        super().__init__()  # Initialize base MediaStreamTrack
        self.cap = cv2.VideoCapture(device)
        if not self.cap.isOpened():
            raise Exception("Could not open video source")

    async def recv(self):
        """
        A coroutine that yields video frames to the WebRTC connection.
        """
        frame_ready, frame = self.cap.read()
        if not frame_ready:
            logging.warning("Empty frame received from webcam")
            return

        # Convert the image to BGR format which is what aiortc uses
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

async def run_offer(pc, offer):
    """
    Negotiate the WebRTC offer received from the client.
    """
    await pc.setRemoteDescription(offer)
    for t in pc.getTransceivers():
        if t.kind == "video":
            pc.addTrack(VideoCamera())

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return pc.localDescription

from aiohttp import web
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
import logging

logging.basicConfig(level=logging.DEBUG)

async def offer(request):
    """
    Handle POST request from the client offering to start a WebRTC connection.
    """
    try:
        params = await request.json()  # Attempt to parse the JSON
    except Exception as e:
        logging.error("Failed to parse JSON from request: %s", e)
        return web.Response(status=400, text="Invalid JSON")

    if "sdp" not in params or "type" not in params:
        logging.error("Missing 'sdp' or 'type' in request")
        return web.Response(status=400, text="Missing 'sdp' or 'type'")

    try:
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        pc = RTCPeerConnection()
        pc_id = f"PeerConnection({id(pc)})"
        pcs.add(pc)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print(f"{pc_id} ICE connection state is {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed":
                await pc.close()
                pcs.discard(pc)

        answer = await run_offer(pc, offer)
        return web.json_response({
            "sdp": answer.sdp,
            "type": answer.type
        })
    except Exception as e:
        logging.error("Failed to handle offer: %s", e)
        return web.Response(status=500, text="Internal server error")


async def main():
    """
    Create an HTTP server that listens for offers.
    """
    app = web.Application()
    app.router.add_post("/offer", offer)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    # Run forever
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass

    # Cleanup
    for pc in pcs:
        await pc.close()
    await runner.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    pcs = set()
    asyncio.run(main())
