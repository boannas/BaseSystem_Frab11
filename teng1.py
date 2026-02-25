import asyncio
import websockets
import json

async def handler(websocket):
    print("React Client Connected!")
    try:
        async for message in websocket:
            data = json.loads(message)

            print("[Received]", data)

# ---------------------------------------------------------
            # connect_port
            if data.get("mode") == "Connect":
                if data.get("action") == "connect_port":
                    port_number = data.get("port")
                    print(f"[Device] Attempting to connect hardware on Port: {port_number}")
                    
                    await asyncio.sleep(1)
                    msg = f"Can't connect to COM{port_number}"
                    sta = "failed"

                    if port_number == 3:
                        msg = f"Connected to COM{port_number}!"
                        sta = "success"
                    
                    response_data = {
                        "mode": "Connect",
                        "status": sta,
                        "message": msg
                    }

                    print("[Response]", response_data)

                    await websocket.send(json.dumps(response_data))
# ---------------------------------------------------------
            elif data.get("mode") == "Home":
                if data.get("action") == "go_home":

                    response_data = {
                        "mode": "Home",
                        "status": "success",
                        "message": "Go home"
                    }

                    print("[Respose]", response_data)

                    await websocket.send(json.dumps(response_data))

            elif data.get("mode") == "Stop":
                if data.get("action") == "stop":

                    response_data = {
                        "mode": "Stop",
                        "status": "success",
                        "message": "STOP"
                    }

                    print("[Respose]", response_data)

                    await websocket.send(json.dumps(response_data))
            
            else:
                response_data = {
                    "status": "failed",
                    "message": "Incorrect request"
                }

                print("[Respose]", response_data)

                await websocket.send(json.dumps(response_data))
                
    except websockets.exceptions.ConnectionClosed:
        print("React Client Disconnected")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket Server is running on ws://localhost:8765...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())