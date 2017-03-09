#!/usr/bin/env python

import paho.mqtt.client as client
from time import sleep, time
import yaml
import serial
import os
import json

PERIOD = 0.01
MAX = 100

if __name__ == '__main__':
    
    f = open('./agent.yaml', 'r')

    conf = yaml.load(f)
    cpe = conf['cpe']
    location = conf['location']
    mqtt = conf['mqtt']
    topic = mqtt['topic']

    client = client.Client()
    client.connect(host=mqtt['host'], port=mqtt['port'], keepalive=60)

    # FTDI driver
    ftdi_list = os.listdir('/dev/serial/by-id')

    dev_list = []
    for ftdi in ftdi_list:
        path = '/dev/serial/by-id/{}'.format(ftdi)
        tty = os.path.realpath(path)  # symbolic link
        ser = serial.Serial(tty)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Protocol operation
        ser.write('STP\n')
        ser.write('WHO\n')
        device_id = ser.readline()[:-1]
        ser.write('STA\n')
        print('device detected: {}'.format(device_id))

        usb = tty.split('/')[2]
        dev_list.append((device_id, ftdi, usb, ser))

    cnt = 0

    while True:
        sleep(PERIOD)
        for dev in dev_list:
            device_id = dev[0]
            usb = dev[2]
            ser = dev[3]
            if ser.in_waiting > 0:
                raw_data = ser.readline()[:-1]
                data = dict(timestamp='{0:.2f}'.format(time()),
                            device_id=device_id,
                            cpe=cpe,
                            location=location,
                            usb=usb,
                            data=raw_data)
                client.publish(topic, json.dumps(data))
            else:
                if cnt > MAX:
                    ser.write('STA\n')
                    cnt = 0
                else:
                    cnt += 1

