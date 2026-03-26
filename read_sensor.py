import sys
sys.path.insert(0, './sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel

def main():
    error, device_list = sensel.getDeviceList()
    if device_list.num_devices == 0:
        print("No Sensel device found")
        return

    err, handle = sensel.openDeviceByID(device_list.devices[0].idx)
    err, info = sensel.getSensorInfo(handle)
    rows, cols = info.num_rows, info.num_cols

    err, frame = sensel.allocateFrameData(handle)
    sensel.setFrameContent(handle, sensel.FRAME_CONTENT_PRESSURE_MASK | sensel.FRAME_CONTENT_CONTACTS_MASK)
    sensel.startScanning(handle)

    print("Reading sensor — press Ctrl+C to stop\n")
    try:
        while True:
            sensel.readSensor(handle)
            err, num_frames = sensel.getNumAvailableFrames(handle)
            for _ in range(num_frames):
                err = sensel.getFrame(handle, frame)

                # Contacts: position and force of each touch
                if frame.n_contacts > 0:
                    print(f"Contacts: {frame.n_contacts}")
                    for i in range(frame.n_contacts):
                        c = frame.contacts[i]
                        print(f"  [{i}] x={c.x_pos:.1f}mm  y={c.y_pos:.1f}mm  force={c.total_force:.0f}g  state={c.state}")

                # Force frame: flat array of rows*cols floats
                max_force = 0
                max_row, max_col = 0, 0
                for row in range(rows):
                    for col in range(cols):
                        val = frame.force_array[row * cols + col]
                        if val > max_force:
                            max_force = val
                            max_row, max_col = row, col

                if max_force > 0:
                    print(f"  Peak: {max_force:.0f} at row={max_row} col={max_col}")

    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        sensel.stopScanning(handle)
        sensel.freeFrameData(handle, frame)
        sensel.close(handle)

if __name__ == "__main__":
    main()
