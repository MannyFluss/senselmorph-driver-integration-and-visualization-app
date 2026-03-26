import sys
sys.path.insert(0, './sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel

err, dl = sensel.getDeviceList()
print('num_devices:', dl.num_devices)
