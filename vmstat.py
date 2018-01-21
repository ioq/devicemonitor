from deviceinfo import VmStat
import sys
import signal

def signal_handler(signal, frame):
        print(':)')
        vmstat.to_csv()
        vmstat.to_plotly()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

vmstat = VmStat()
vmstat.start()
vmstat.join()
print(":)")