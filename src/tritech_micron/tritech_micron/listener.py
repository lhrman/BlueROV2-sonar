import serial
import threading
import time

def read_from_serial(port, baudrate, log_file, direction):
    with serial.Serial(port, baudrate, timeout=1) as ser:
        print(f"Listening on {port} at {baudrate} baudrate for {direction} data")
        with open(log_file, 'w') as f:
            while True:
                data = ser.read(ser.in_waiting or 1)
                if data:
                    hex_data = data.hex()
                    print(f"{direction} data: {hex_data}")
                    f.write(f"{direction} data: {hex_data}\n")

def main():
    serial_port = '/dev/ttyUSB0'
    baud_rate = 115200
    
    # Start threads to log RX and TX data
    rx_thread = threading.Thread(target=read_from_serial, args=(serial_port, baud_rate, 'rx_log.txt', 'RX'))
    rx_thread.daemon = True
    rx_thread.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Serial logging stopped.')

if __name__ == "__main__":
    main()
