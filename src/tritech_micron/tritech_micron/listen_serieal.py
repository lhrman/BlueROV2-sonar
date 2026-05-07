import serial
# import threading

def read_from_serial(port='/dev/ttyUSB0', baudrate=9600):
    print(f"baudrate: {baudrate}")
    # Open the serial port
    with serial.Serial(port, baudrate, timeout=1) as ser:
        print(f"Listening on {port} at {baudrate} baudrate")
        
        while True:
            # Read data from the serial port
            data = ser.read(ser.in_waiting or 1)
            
            if data:
                # Convert the data to hexadecimal format
                hex_data = data.hex()
                print(f"Received data: {hex_data}")

# Start logging threads
# tx_thread = threading.Thread(target=read_from_serial)
# tx_thread.daemon = True
# tx_thread.start()

# try:
#     while True:
#         # Keep main thread alive
#         pass
# except KeyboardInterrupt:
#     print('Serial connection closed.')

if __name__ == "__main__":
    read_from_serial()