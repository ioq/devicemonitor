import threading
import subprocess
import datetime
import time
import re
import signal
import sys
import pandas as pd
from abc import ABC, abstractmethod
import plotly.offline as py
import plotly.graph_objs as go
from plotly import tools

class DeviceInfo(ABC, threading.Thread):
    def __init__(self, name="deviceinfo"):
        threading.Thread.__init__(self)
        self._name = name
        self._data = None
        self._now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    @abstractmethod
    def _get_device_info(self):
        pass

    def run(self):
        self._get_device_info()

    def get_info(self):
        return self._data

    @abstractmethod
    def to_plotly(self):
        pass

    def to_csv(self):
        if self._data is None:
            return

        name = self._now + "_" + self._name + ".csv"
        self._data.to_csv(name)

class Meminfo(DeviceInfo):
    def __init__(self):
        DeviceInfo.__init__(self, "meminfo")
        self.__stop = False

    def __get_mem_item(self, name, line):
        reg = "^(" + name + ":)" + "(\s{1,})(\d{1,})"
        r = re.compile(reg)
        s = r.search(line)
        if s is not None:
            return round(int(s.group(3))/1024, 2)
        else:
            return None
    
    def quit(self):
        self.__stop = True

    def _get_device_info(self):
        items = [
            "MemTotal",
            "MemFree",
            "Buffers",
            "Cached",
            "Mapped",
            "SwapTotal",
            "SwapFree",
        ]

        while self.__stop is False:
            cmd = ["adb", "shell", "cat", "/proc/meminfo"]
            try:
                #proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                print(e)
                self.to_csv()
                self.to_plotly()
                return

            d = {}
            while True:
                line = proc.stderr.readline().strip()
                if len(line) is not 0:
                    print(line)
                    self.to_csv()
                    self.to_plotly()
                    return

                line = proc.stdout.readline().strip()
                if len(line) is 0:
                    break
                try:
                    line = str(line, encoding = "utf-8")
                except UnicodeDecodeError as e:
                    print(e)
                    continue

                for item in items:
                    size = self.__get_mem_item(item, line)
                    if size is not None:
                        d[item] = size 
                        break

            #get swap
            d["Swap"] = d["SwapTotal"] - d["SwapFree"]
            del d["SwapTotal"]
            del d["SwapFree"]
            
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            d_meminfo = {now: d} 
            df = pd.DataFrame.from_dict(d_meminfo, orient="index")
            self._data = pd.concat([self._data, df])
            self.__dump()
            time.sleep(1)

    def __dump(self):
        print(self._data.tail(n=32))        

    def to_plotly(self):
        data = []
        for i in self._data.columns:
            trace = go.Scatter(
                x = self._data.index,
                y = self._data[i],
                name = i,
            )

            data.append(trace)

        layout = go.Layout(
            title = "Device MemInfo",
            yaxis = dict(
                    title = "memory usage(MB)"
                ),
        )

        fig = go.Figure(data=data, layout=layout)
        filename = self._now + '_' + self._name +".html" 
        py.plot(fig, filename=filename, auto_open=True)
        

class VmStat(DeviceInfo):
    def __init__(self):
        DeviceInfo.__init__(self, "vmstat")

    def to_plotly(self):
        data_cpu = []
        name = ["us", "sy", "wa", "cpu_u"]
        for i in name:
            trace = go.Scatter(
                x = self._data.index,
                y = self._data[i],
                name = i,
            )

            data_cpu.append(trace)


        data_memory = []
        name = ["swap","free","buffer","cache"]
        for i in name:
            trace = go.Scatter(
                x = self._data.index,
                y = self._data[i],
                name = i,
            )

            data_memory.append(trace)
        
        data_io = []
        name = ["si","so","bi","bo"]
        for i in name:
            trace = go.Scatter(
                x = self._data.index,
                y = self._data[i],
                name = i,
            )

            data_io.append(trace)

        fig = tools.make_subplots(
            rows=3, 
            cols=1,
            subplot_titles=(
                'CPU Info', 
                'Memory Info',
                'IO Info', )
            )
        fig['layout']['yaxis1'].update(title='Usage(%)')
        fig['layout']['yaxis2'].update(title='Memory Usage(MB)')
        fig['layout']['yaxis3'].update(title='IO Through(KB)')

        for i in data_cpu:
            fig.append_trace(i, 1,1)
        for i in data_memory:
            fig.append_trace(i, 2,1)
        for i in data_io:
            fig.append_trace(i, 3,1)


        filename = self._now + '_' + self._name +".html" 
        py.plot(fig, filename=filename, auto_open=True)

    def _get_device_info(self):
        cmd = ["adb", "shell", "vmstat", "1"]
        try:
            #proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except OSError as e:
            print(e)
            return

        while True:
            line = proc.stdout.readline().strip()
            if len(line) is 0:
                self.to_plotly()
                self.to_plotly()
                break
            try:
                line = str(line, encoding = "utf-8")
            except UnicodeDecodeError as e:
                print(e)
                continue

            print(line)
            source = re.split(r'\s{1,}', line)
            '''
            procs -----------memory---------- ---swap-- -----io---- -system-- ----cpu----
            r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa
            0  0 616392 178468 105700 627320   12   19  1018   232    0  680 26 14 59  0
            '''
            if line.isprintable() is False:
                continue    
            if len(source) is not 16:
                continue
            if source[0] == 'procs':
                continue
            if source[2] == 'swpd':
                continue

            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            d = {
                now:
                {
                    "r":source[0],
                    "b":source[1],
                    "swap":round(int(source[2])/1024,2),
                    "free":round(int(source[3])/1024,2),
                    "buffer":round(int(source[4])/1024,2),
                    "cache":round(int(source[5])/1024,2),
                    "si":source[6],
                    "so":source[7],
                    "bi":source[8],
                    "bo":source[9],
                    "in":source[10],
                    "cs":source[11],
                    "us":int(source[12]),
                    "sy":int(source[13]),
                    "id":int(source[14]),
                    "wa":int(source[15]),
                    "cpu_u": (int(source[12]) + int(source[13]))
                }
            }
            df = pd.DataFrame.from_dict(d, orient="index")
            self._data = pd.concat([self._data, df])
           