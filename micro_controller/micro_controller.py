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
import asyncio
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from go2_webrtc_driver.constants import RTC_TOPIC, SPORT_CMD
import logging
import aioserial
import time 

logging.basicConfig(level=logging.ERROR)

async def read_microbit_serial(queue, port='/dev/tty.usbmodem143202', baudrate=9600):
    ser = aioserial.AioSerial(port, baudrate, timeout=0.1)

    try:
        ser.reset_input_buffer()
        while True:
            await asyncio.sleep(0.1)

            if ser.in_waiting > 0:
                line = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                if ',' in line:
                    command, value = line.split(',', 1)
                    print(f"Received from Serial: Command: {command.strip()}, Value: {value.strip()}")
                    await queue.put((command.strip(), value.strip()))
                else:
                    print(f"Invalid Line: {line}")
    except Exception as e:
        print(f"Serial reading error: {e}")
    finally:
        ser.close()

async def handle_commands(queue, conn):
    while True:
        command, value = await queue.get()  
        print(f"Handling command: {command}, with value: {value}")
        try:
            if command == "Move":
                x_value = float(value)
                x = 0.5 if x_value >= 120 else -0.5 if x_value <= -120 else 0
                print(f"Executing Move command with x: {x}")
                await conn.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Move"], "parameter": {"x": x, "y": 0, "z": 0}}
                )
        except ValueError as e:
            print(f"Error processing command: {e}")
        finally:
            queue.task_done()

async def main():
    queue = asyncio.Queue()
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.55")
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
        await conn.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")