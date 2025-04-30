'''import asyncio
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD
import logging
import aioserial
import time 

logging.basicConfig(level=logging.ERROR)

async def read_microbit_serial(port='/dev/tty.usbmodem143202', baudrate=9600):
    ser = aioserial.AioSerial(port, baudrate, timeout=0.1)

    try:
        ser.reset_input_buffer()
        while True:
            time.sleep(0.1)

            if ser.in_waiting > 0:
                line = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                if ',' in line:
                    command, value = line.split(',',1)
                    print(f"Command: {command.strip()}, Value: {value.strip()}")
                else:
                    print(f"Invalid Line: {line}")
    except KeyboardInterrupt:
        print("\nSerial reading stopped.")

async def handle_commands(queue, conn):
    while True:
        command, value = await queue.get()  
        print(f"Handling command: {command}, with value: {value}")
        if command == "Move":
            x_value = float(value)
            x = 2 if x_value >= 120 else -2 if x_value <= -120 else 0
            print(f"Executing Move command with x: {x}")
            await conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["Move"], "parameter": {"x": x, "y": 0, "z": 0}}
            )

async def main():
    queue = asyncio.Queue()
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.55")
    await conn.connect()
    
   

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
'''
import os
import sys
current_script_path = os.path.dirname(__file__)
file_path = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
sys.path.append(file_path)
import asyncio
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD
import logging
import aioserial
import time 

logging.basicConfig(level=logging.FATAL)

async def read_microbit_serial(queue, port='/dev/ttyACM0', baudrate=9600):
    ser = aioserial.AioSerial(port, baudrate, timeout=0.1)
    buffer = ''
    try:
        ser.reset_input_buffer()
        while True:
            await asyncio.sleep(0.1)

            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                
                while '\n' in buffer:
                    line,buffer = buffer.split("\n",1)
                    if ',' in line:
                        command, value = line.split(',', 1)
                        x_val,y_val,z_val = value.split(',', 2)
                        move_value = x_val,y_val,z_val
                        print(f"Received from Serial: Command: {command.strip()}, X Value: {x_val.strip()}, Y Value: {y_val.strip()}, Z Value: {z_val.strip()}")
                        await queue.put((command.strip(), x_val.strip(), y_val.strip(), z_val.strip()))
                    elif line.strip():
                        await queue.put((line.strip(), None, None, None),)
                        print(f"Received Standalone Command: {line.strip()}")
                    else:
                        print(f"Invalid Line: {line}")
    except Exception as e:
        print(f"Serial reading error: {e}")
    finally:
        ser.close()

async def handle_commands(queue, conn):
    while True:
        command, x_val, y_val, z_val = await queue.get()
        print(f"Handling command: {command}, x: {x_val}, y: {y_val}, z: {z_val}")
        try:
            if command == "Move":
                x_value = float(x_val)
                y_value = float(y_val)
                z_value = float(z_val)

                print(f"Executing Move command with x: {x_value}, y: {y_value}, z: {z_value}")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Move"], "parameter": {"x": x_value, "y": y_value, "z": z_value}}
                )
            elif command in {"Sit", "RiseSit", "Stretch","Wallow","StandUp","Dance1","Dance2","FrontJump","FrontPounce"}:
                print(f"Performing {command}")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD[command]}
                )
            elif command in {"normal", "ai"}:
                print(f"Switching motion mode to '{command}'...")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["MOTION_SWITCHER"],
                    {
                        "api_id": 1002,  
                        "parameter": {"name": command}
                    }
                )
            elif command == "Handstand":
                print("Switching to Hanstand Mode...")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["StandOut"],
                        "parameter": {"data": True}
                        }
                    )
            elif command == "StandDown":
                print("Switching to StandUp Mode...")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["StandOut"],
                        "parameter": {"data": False}
                        }
                    )
            elif command == "ObstacleOn":
                print("Enabling obstacle avoidance...")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["OBSTACLES_AVOID"],
                    {
                        "api_id": 1001,
                        "parameter": {"enable":True}
                        })
                
            elif command == "ObstacleOff":
                print("Disabling obstacle avoidance...")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["OBSTACLES_AVOID"],
                    {
                        "api_id": 1001,
                        "parameter": {"enable":False}
                        })
        except ValueError as e:
            print(f"Error processing command: {e}")
        finally:
            queue.task_done()


async def main():
    queue = asyncio.Queue()
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.0.129")
    await conn.connect()
    
  
    serial_task = asyncio.create_task(read_microbit_serial(queue))
    command_task = asyncio.create_task(handle_commands(queue, conn))
    
    try:
        await asyncio.gather(serial_task, command_task)
    except asyncio.CancelledError:
        print("\nTasks were cancelled")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pass#await conn.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
