from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import traceback

router = APIRouter(prefix="/stream", tags=["Streaming"])

@router.websocket("/audio/{session_id}")
async def audio_stream(ws: WebSocket, session_id: str):
    await ws.accept()
    print(f"🔵 Client connected to audio stream: {session_id}")

    try:
        while True:
            msg = await ws.receive()   # returns dict with keys: 'type', 'text' or 'bytes'
            # msg example: {'type':'websocket.receive', 'bytes': b'...'}
            if 'bytes' in msg and msg['bytes'] is not None:
                chunk = msg['bytes']
                # process chunk (write to temp file or buffer)
                # for now we respond with confirmation (non-blocking)
                try:
                    await ws.send_text("chunk_received")
                except Exception as e:
                    print("send_text failed:", e)

            elif 'text' in msg and msg['text'] is not None:
                text = msg['text']
                # control commands from client like "flush"
                if text == "flush":
                    # process flush (e.g., run inference on current buffer)
                    try:
                        await ws.send_text("flush_received")
                    except Exception:
                        pass
                else:
                    # optionally echo or ignore
                    await ws.send_text(f"server_received_text:{text}")
            elif msg.get("type") == "websocket.disconnect":
                print("Client requested disconnect")
                break
            else:
                # unexpected shape
                print("Unexpected websocket message:", msg)
    except WebSocketDisconnect:
        print(f"🔴 Client disconnected: {session_id}")
    except Exception:
        print("Exception in audio_stream handler:")
        traceback.print_exc()
    finally:
        try:
            await ws.close()
        except Exception:
            pass
        print(f"[audio] cleanup done for {session_id}")

@router.websocket("/video/{session_id}")
async def video_stream(ws: WebSocket, session_id: str):
    await ws.accept()
    print(f"🟣 Client connected to video stream: {session_id}")

    try:
        while True:
            msg = await ws.receive()

            if 'bytes' in msg and msg['bytes'] is not None:
                chunk = msg['bytes']
                # process video chunk
                await ws.send_text("frame_received")

            elif 'text' in msg and msg['text'] is not None:
                text = msg['text']
                if text == "flush":
                    await ws.send_text("flush_done")

            elif msg.get("type") == "websocket.disconnect":
                print("Video stream disconnected")
                break

    except WebSocketDisconnect:
        print("🔴 Video client disconnected")
    except Exception as e:
        print("ERROR in video_stream:", e)
    finally:
        try:
            await ws.close()
        except:
            pass
        print("[video] cleanup done")