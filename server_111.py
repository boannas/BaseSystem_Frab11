# server.py
import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
from protocol import Protocol
import time

# One Protocol instance owns Modbus + decode logic
protocol = Protocol()

# Keep only what the websocket server needs
server_state = {
    "stats_task": None,   
}

robot_state = {
    "position": "--",
    "speed": "--",
    "accel": "--",
    "gripper_z": "Idle",
    "gripper_jaw": "Idle",
    "mode": "Idle",
    "emergency": "Idle",
}

modbus_lock = asyncio.Lock()

async def stats_loop(websocket):
    last_loop_time = None
    try:
        while True:
            loop_start = time.perf_counter()
            read_latency = None
            if protocol.client and protocol.is_connected():
                async with modbus_lock:

                    read_start = time.perf_counter()
                    ok = await asyncio.to_thread(protocol.routine)
                    read_end = time.perf_counter()
                    read_latency = read_end - read_start

                    if ok:
                        print(protocol.register.registers[:11])
                        robot_state["position"] = protocol.theta_actual_pos
                        robot_state["speed"] = protocol.theta_actual_speed
                        robot_state["accel"] = protocol.theta_actual_accel
                        robot_state["emergency"] = protocol.emergency_stop_status
                        robot_state["mode"] = protocol.moving_status
                        robot_state["gripper_z"] = protocol.gripper_actual_reed1
                        robot_state["gripper_jaw"] = protocol.gripper_actual_reed3

            payload = {
                "type": "STATS",
                "pos": robot_state["position"],
                "speed": robot_state["speed"],
                "accel": robot_state["accel"],
                "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
                "mode": robot_state["mode"],
                "emergency": robot_state["emergency"],
                "connected": bool(protocol.client) and protocol.is_connected(),
            }
            # ---- measure send time ----
            send_start = time.perf_counter()
            try:
                await websocket.send(json.dumps(payload))
            except ConnectionClosed:
                break
            send_end = time.perf_counter()
            send_latency = send_end - send_start
            loop_end = time.perf_counter()

            # if last_loop_time is not None:
            #     dt = loop_end - last_loop_time
            #     freq = 1.0 / dt if dt > 0 else 0

            #     print(
            #         f"Loop dt: {dt:.4f}s | "
            #         f"Read: {read_latency*1000:.2f} ms | "
            #         f"Send: {send_latency*1000:.2f} ms"
            #     )
            last_loop_time = loop_end
            # await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass

async def handler(websocket: websockets.WebSocketServerProtocol):
    print("React Client Connected!")

    # Ensure only ONE stats loop is active (React dev mode can connect twice)
    old = server_state.get("stats_task")
    if old and not old.done():
        old.cancel()
        try:
            await old
        except asyncio.CancelledError:
            pass

    stats_task = asyncio.create_task(stats_loop(websocket))
    server_state["stats_task"] = stats_task

    initial_stats = {
        "type": "STATS",
        "message": "Connected to Python Backend",
        "pos": robot_state["position"],
        "speed": robot_state["speed"],
        "accel": robot_state["accel"],
        "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
        "mode": robot_state["mode"],
        "emergency": robot_state["emergency"],
        "connected": bool(protocol.client) and protocol.is_connected(),
    }

    try:
        await websocket.send(json.dumps(initial_stats))
    except ConnectionClosed:
        stats_task.cancel()
        return

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"mode": "Error", "message": "Invalid JSON"}))
                continue

            req_mode = data.get("mode")
            action = data.get("action")
            # print(f"Received command: mode={req_mode}, action={action}")
            print(data)
            # ---------------- CONNECT / DISCONNECT ----------------
            if req_mode == "Connect" and action == "connect_port":
                port_num = data.get("port")
                com_port = f"COM{port_num}"
                slave = int(data.get("slave", 21))

                # ok = await asyncio.to_thread(protocol.connect_rtu, com_port, slave)

                async with modbus_lock:
                    if protocol.client and protocol.is_connected() and protocol.port == com_port and protocol.slave_address == slave:
                        ok = True
                    else :
                        ok = await asyncio.to_thread(protocol.connect_rtu, com_port, slave)

                await websocket.send(json.dumps({
                    "mode": "Connect",
                    "action": "connect_port",
                    "status": "success" if ok else "failed",
                    "message": f"Connected to {com_port} (slave {slave})" if ok else f"Failed to connect to {com_port}",
                }))
                continue

            # # ---------------- HOME / MODE ----------------
            if req_mode == "Home":
                if action == "go_home":
                    await asyncio.to_thread(protocol.write_base_system_status, "go_home")
                    await websocket.send(json.dumps({"mode": "Home", "status": "success"}))
                    continue
                elif action == "set_home":
                    await asyncio.to_thread(protocol.write_base_system_status, "set_home")
                    await websocket.send(json.dumps({"mode": "Set home", "status": "success"}))
                    continue

            # if req_mode == "Mode" and action == "set":
            #     # Example: "Jog" / "Auto"
            #     value = data.get("value")
            #     if value not in ("Home", "Jog", "Auto"):
            #         await websocket.send(json.dumps({"mode": "Mode", "status": "failed", "message": "Invalid mode"}))
            #         continue
            #     await asyncio.to_thread(protocol.write_base_system_status, value)
            #     await websocket.send(json.dumps({"mode": "Mode", "status": "success", "value": value}))
            #     continue

            # # ---------------- STOP ----------------
            # if req_mode == "Stop" and action == "stop":
            #     await asyncio.to_thread(protocol.write_stop_process, "Stop")
            #     await websocket.send(json.dumps({"mode": "Stop", "status": "success"}))
            #     continue

            # if req_mode == "Stop" and action == "normal":
            #     await asyncio.to_thread(protocol.write_stop_process, "Normal")
            #     await websocket.send(json.dumps({"mode": "Stop", "status": "success"}))
            #     continue

            # # ---------------- GRIPPER ----------------
            # if req_mode == "Gripper" and action == "checkbox":
            #     # value: "Enable" or "Disable"
            #     value = data.get("value", "Disable")
            #     if value not in ("Enable", "Disable"):
            #         await websocket.send(json.dumps({"mode": "Gripper", "status": "failed", "message": "Invalid value"}))
            #         continue
            #     await asyncio.to_thread(protocol.write_gripper_checkbox, value)
            #     await websocket.send(json.dumps({"mode": "Gripper", "status": "success"}))
            #     continue

            # if req_mode == "Gripper" and action == "command":
            #     # value: "Release" / "Grip" / "Pick" / "Place"
            #     value = data.get("value")
            #     if value not in ("Release", "Grip", "Pick", "Place"):
            #         await websocket.send(json.dumps({"mode": "Gripper", "status": "failed", "message": "Invalid command"}))
            #         continue
            #     await asyncio.to_thread(protocol.write_gripper_command, value)
            #     await websocket.send(json.dumps({"mode": "Gripper", "status": "success"}))
            #     continue

            # if req_mode == "Gripper" and action == "movement":
            #     # value: "Forward" / "Backward"
            #     value = data.get("value")
            #     if value not in ("Forward", "Backward"):
            #         await websocket.send(json.dumps({"mode": "Gripper", "status": "failed", "message": "Invalid movement"}))
            #         continue
            #     await asyncio.to_thread(protocol.write_gripper_movement, value)
            #     await websocket.send(json.dumps({"mode": "Gripper", "status": "success"}))
            #     continue

            # # ---------------- MANUAL / PTP ----------------
            # if req_mode == "Manual" and action == "ptp":
            #     # ptp_mode: "Index" or "Position"
            #     ptp_mode = data.get("ptp_mode", "Position")
            #     value = data.get("value", 0)
            #     repeat = int(data.get("repeat", 0))

            #     if ptp_mode not in ("Index", "Position"):
            #         await websocket.send(json.dumps({"mode": "Manual", "status": "failed", "message": "Invalid ptp_mode"}))
            #         continue

            #     try:
            #         value_f = float(value)
            #     except Exception:
            #         await websocket.send(json.dumps({"mode": "Manual", "status": "failed", "message": "Invalid value"}))
            #         continue

            #     await asyncio.to_thread(protocol.write_point_to_point, ptp_mode, value_f, repeat)
            #     await websocket.send(json.dumps({"mode": "Manual", "status": "success"}))
            #     continue

            # ---------------- FALLBACK ----------------
            await websocket.send(json.dumps({
                "mode": "Error",
                "message": f"Unsupported command: mode={req_mode}, action={action}"
            }))

    except websockets.exceptions.ConnectionClosed:
        print("Frontend client disconnected.")
    finally:
        # Always stop stats loop for this websocket
        stats_task.cancel()
        try:
            await stats_task
        except asyncio.CancelledError:
            pass
        # Keep Modbus connected across UI reconnects (recommended)
        # If you want to disconnect Modbus when UI closes, uncomment:
        # await asyncio.to_thread(protocol.disconnect)


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket Server running ws://localhost:8765")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())