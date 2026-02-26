import asyncio
import websockets
import json

robot_state = {
    "position": 0,
    "speed": 0,
    "accel": 0,
    "gripper_z": "Up",     # "Up" or "Down"
    "gripper_jaw": "Close", # "Open" or "Close"
    "mode": "Manual",
    "emergency": "Normal"
}

async def handler(websocket):
    print("React Client Connected!")

    initial_stats = {
        "type": "STATS",
        "message": "Connected to Python Backend",
        "pos": robot_state["position"],
        "speed": robot_state["speed"],
        "accel": robot_state["accel"],
        "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
        "mode": robot_state["mode"],
        "emergency": robot_state["emergency"]
    }
    await websocket.send(json.dumps(initial_stats))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"[Received] {data}")

                req_mode = data.get("mode")
                action = data.get("action")

                # --- Handle Connect ---
                if req_mode == "Connect":
                    if action == "connect_port" and data.get("port") == 3:
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": f"Connect to port {data.get('port')}",
                        }

                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                    else:
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "failed",
                            "message": f"Failed to connect to port {data.get('port')}",
                        }

                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                # --- Handle HOME Actions ---
                elif req_mode == "Home":
                    # Set Home
                    if action == "set_home":
                        offset = data.get("offset_angle")
                        msg = f"Setting home position" if offset is not None else "Home set to current position"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))
                    
                    # Go Home
                    elif action == "go_home":
                        msg = "Returning to Home Position"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                # --- Handle STOP Action ---
                elif req_mode == "Stop" and action == "stop":
                    robot_state["mode"] = "STOPPED"
                    
                    msg = "Stopped"
                    payload = {
                        "mode": req_mode,
                        "action": action,
                        "status": "success",
                        "message": msg,
                    }

                    await websocket.send(json.dumps(payload))

                    update_payload = {
                        "type": "STATS",
                        "mode": robot_state["mode"],
                        "message": "EMERGENCY STOP ACTIVATED",
                    }

                    print(f"[Update] {update_payload}")
                    print(f"[Sending] {payload}")
                    await websocket.send(json.dumps(update_payload))

                # --- Handle Manual ---
                elif req_mode in ["Gripper", "Manual"]:
                    # Gripper
                    gripper_action = [
                        "gripper_down", "gripper_up", 
                        "gripper_open", "gripper_close", 
                        "gripper_pick", "gripper_place"
                    ]
                    
                    if action in gripper_action:
                        # Update Mock State
                        if action == "gripper_up":
                            robot_state["gripper_z"] = "Up"
                        elif action == "gripper_down":
                            robot_state["gripper_z"] = "Down"
                        elif action == "gripper_open":
                            robot_state["gripper_jaw"] = "Open"
                        elif action == "gripper_close":
                            robot_state["gripper_jaw"] = "Close"
                        elif action == "gripper_pick":
                            robot_state["gripper_z"] = "Up"
                            robot_state["gripper_jaw"] = "Close"
                        elif action == "gripper_place":
                            robot_state["gripper_z"] = "Up"
                            robot_state["gripper_jaw"] = "Open"

                        # Send flattened STATS + LOG message back
                        update_payload = {
                            "type": "STATS",
                            "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
                            "message": f"Executed: {action}",
                        }
                        print(f"[Update] {update_payload}")
                        await websocket.send(json.dumps(update_payload))

                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": f"{action}",
                        }

                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                    # Jog
                    elif action == "jog":
                        dir = data.get("direction")
                        degree = float(data.get("value", 0))
                        msg = f"Joc {dir} {degree} deg"

                        if dir == "CW":
                            robot_state["position"] += degree
                        else:
                            robot_state["position"] -= degree

                        robot_state["position"] = robot_state["position"] % 360

                        jog_payload = {
                            "type": "STATS",
                            "pos": robot_state["position"],
                            "message": f"Jogged {degree}° {action[-3:].upper()}",
                        }
                        print(f"[Update] {jog_payload}")
                        await websocket.send(json.dumps(jog_payload))

                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }

                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                # --- Handle Auto ---
                elif req_mode in ["Auto"]:
                    # pick and place
                    if action == "pick_place":
                        msg = "Pick and Place"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                    # point to point
                    elif action == "point_to_point":
                        msg = "Point to Point"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                # --- Handle TEST ---
                elif req_mode in ["Test"]:
                    # performance
                    if action == "performance":
                        msg = "Performance test"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                    # precision
                    if action == "precision":
                        msg = "Precision test"
                        payload = {
                            "mode": req_mode,
                            "action": action,
                            "status": "success",
                            "message": msg,
                        }
                        print(f"[Sending] {payload}")
                        await websocket.send(json.dumps(payload))

                else:
                    msg = "Point to Point"
                    payload = {
                        "mode": "Error",
                        "message": "Invalid command",
                    }
                    print(f"[Sending] {payload}")
                    await websocket.send(json.dumps(payload))


            except json.JSONDecodeError:
                print("Error: Invalid JSON received")

            print("----"*10)

    except websockets.exceptions.ConnectionClosed:
        print("Frontend client disconnected.")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket Server is running on ws://localhost:8765...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())