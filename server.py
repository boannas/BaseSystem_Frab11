import asyncio
import json
import websockets
from pymodbus.client import ModbusSerialClient
import time
from protocol import Protocol
from websockets.exceptions import ConnectionClosed

protocol = Protocol()

server_state = {
    "client": None,
    "connected": False,
    "port": None,
    "slave": 21,
}

robot_state = {
    "position": '--',
    "speed": '--',
    "accel": '--',
    "gripper_z": "Idle",     # "Up" or "Down"
    "gripper_jaw": "Idle", # "Open" or "Close"
    "mode": "Idle",
    "emergency": "Idle"
}


# # For testing: print log in the server console instead of sending to frontend
# async def stats_loop(websocket):
#     last_read_time = None

#     try:
#         while True:

#             if protocol.client and protocol.is_connected():
#                 try:
#                     t_start = time.perf_counter()

#                     rr = await asyncio.to_thread(
#                         protocol.client.read_holding_registers,
#                         0, 10,
#                         slave=server_state["slave"]
#                     )

#                     t_end = time.perf_counter()
#                     print(rr)
#                     print("Registers:", rr.registers)

#                     if rr and (not rr.isError()) and hasattr(rr, "registers"):
#                         now = t_end

#                         if last_read_time is not None:
#                             dt = now - last_read_time

#                         last_read_time = now

#                         print("Registers:", rr.registers)

#                         if len(rr.registers) >= 3:
#                             # robot_state["position"] = rr.registers[0]
#                             robot_state["speed"]    = rr.registers[1]
#                             robot_state["accel"]    = rr.registers[2]

#                             # robot_state["mode"] = "Auto" if rr.registers[3] == 1 else "Manual"
#                             # robot_state["emergency"] = "Yes" if rr.registers[4] == 1 else "No"
#                             # robot_state["gripper_z"] = "Down" if rr.registers[5] == 1 else "Up"
#                             # robot_state["gripper_jaw"] = "Close" if rr.registers[6] == 1 else "Open"

#                         # print(f"dt between Modbus responses: {dt:.4f} s  ({1/dt:.2f} Hz)")
#                         # print(f"Read latency: {(t_end - t_start)*1000:.2f} ms")
#                     protocol.write_heartbeat()
#                 except Exception as e:
#                     print(f"Error reading Modbus registers: {e}")

#             payload = {
#                 "type": "STATS",
#                 "pos": robot_state["position"],
#                 "speed": robot_state["speed"],
#                 "accel": robot_state["accel"],
#                 "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
#                 "mode": robot_state["mode"],
#                 "emergency": robot_state["emergency"]
#             }

#             try:
#                 await websocket.send(json.dumps(payload))
#             except ConnectionClosed:
#                 break

#             await asyncio.sleep(0.1)  # IMPORTANT: control polling rate

#     except asyncio.CancelledError:
#         pass

async def stats_loop(websocket):
    try:
        while True:
            # Poll modbus through Protocol
            ok = await asyncio.to_thread(protocol.routine)

            if protocol.client and protocol.is_connected():
                print(protocol.theta_actual_pos, protocol.theta_actual_accel, protocol.theta_actual_speed)
                if ok:
                    # Example mapping (adjust to your real register meaning)
                    robot_state["position"] = getattr(protocol, "theta_actual_pos", "--")
                    robot_state["speed"]    = getattr(protocol, "theta_actual_speed", "--")
                    robot_state["accel"]    = getattr(protocol, "theta_actual_accel", "--")

                    # emergency
                    robot_state["emergency"] = getattr(protocol, "emergency_stop_status", "0")

                    # gripper (you currently store reed bits as strings)
                    robot_state["gripper_z"] = f"Reed1:{protocol.gripper_actual_reed1}"
                    robot_state["gripper_jaw"] = f"Reed2:{protocol.gripper_actual_reed2}"

                    # optional heartbeat
                    # await asyncio.to_thread(protocol.write_heartbeat)

            payload = {
                "type": "STATS",
                "pos": robot_state["position"],
                "speed": robot_state["speed"],
                "accel": robot_state["accel"],
                "gripper": f"{robot_state['gripper_z']} / {robot_state['gripper_jaw']}",
                "mode": robot_state["mode"],
                "emergency": robot_state["emergency"],
                "connected": protocol.is_connected() if protocol.client else False,
            }

            try:
                await websocket.send(json.dumps(payload))
            except ConnectionClosed:
                break

            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        pass


async def handler(websocket):
    print("React Client Connected!")
    stats_task = asyncio.create_task(stats_loop(websocket))

    # Send initial stats to frontend
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
                req_mode = data.get("mode")
                action = data.get("action")
                print(f"Received command: mode={req_mode}, action={action}")
                
                # CONNECT
                if req_mode == "Connect" and action == "connect_port":
                    port_num = data.get("port")         
                    com_port = f"COM{port_num}"
                    slave = int(data.get("slave", 21))         

                    ok = await asyncio.to_thread(protocol.connect_rtu, com_port, slave)

                    # # Close old connection if any
                    # old = server_state["client"]
                    # if old:
                    #     try:
                    #         await asyncio.to_thread(old.close)
                    #     except Exception:
                    #         pass
                    #     server_state["client"] = None
                    #     server_state["connected"] = False

                    # client = ModbusSerialClient(
                    #     port=com_port,
                    #     baudrate=19200,
                    #     parity="E",
                    #     stopbits=1,
                    #     bytesize=8,
                    #     timeout=1,
                    # )

                    await websocket.send(json.dumps({
                        "mode": "Connect",
                        "action": "connect_port",
                        "status": "success" if ok else "failed",
                        "message": f"Connected to {com_port} (slave {slave})" if ok else f"Failed to connect to {com_port}",
                    }))
                    continue

                    # ok = await asyncio.to_thread(client.connect)    # Connect in thread to avoid blocking event loop

                    # if ok:  # Successful connection with the serial port
                    #     server_state["client"] = client
                    #     server_state["connected"] = True
                    #     server_state["port"] = com_port

                    #     print(f"Connected to {com_port}, started Modbus!!!!!")
                    #     payload = {
                    #         "mode": "Connect",
                    #         "action": "connect_port",
                    #         "status": "success",
                    #         "message": f"Connected to {com_port}",
                    #     }
                    # else:
                    #     try:
                    #         await asyncio.to_thread(client.close)
                    #     except Exception:
                    #         pass

                    #     payload = {
                    #         "mode": "Connect",
                    #         "action": "connect_port",
                    #         "status": "failed",
                    #         "message": f"Failed to connect to {com_port}",
                    #     }
                    #     print(f"Failed to connect to {com_port}")

                    # await websocket.send(json.dumps(payload))
                    # continue 

                # HOME
                elif req_mode == "Home":
                    pass

                # STOP
                elif req_mode == "Stop" and action == "stop":
                    pass 

                # GRIPPER/MANUAL
                elif req_mode in ["Gripper", "Manual"]:
                    pass
                
                # AUTO
                elif req_mode == "Auto":
                    pass

                # TEST (Performance test)
                elif req_mode == "Test":
                    pass

                else:
                    pass

                # Everything else (for now)
                await websocket.send(json.dumps({
                    "mode": "Error",
                    "message": "Unsupported command"
                }))

            except json.JSONDecodeError:
                print("Received invalid JSON.")

    except websockets.exceptions.ConnectionClosed:
        print("Frontend client disconnected.")

    finally:

        # Stop STATS loop
        stats_task.cancel()  
        try:
            await stats_task
        except asyncio.CancelledError:
            pass

        # # Clean up on disconnect
        # client = server_state["client"]
        # if client:
        #     try:
        #         await asyncio.to_thread(client.close)
        #     except Exception:
        #         pass
        # server_state["client"] = None
        # server_state["connected"] = False
        # print("Cleaned up server state.")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket Server running ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())