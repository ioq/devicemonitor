from deviceinfo import MemInfo
import sys
import signal

def signal_handler(signal, frame):
        print(':)')
        meminfo.quit()
        meminfo.to_csv()
        meminfo.to_plotly()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

meminfo = MemInfo()
meminfo.start()
meminfo.join()
print(":)")
