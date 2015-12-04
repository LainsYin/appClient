#!/usr/bin/env python2.7
# -*-coding:utf-8 -*-

import sys
import time
import socket
import signal
import json
import struct
import logging
import threading
from struct import pack, unpack

STOP = False
THREADS = []


def init_log():
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s - %(process)-6d - %(threadName)-10s - %(levelname)-8s]\t%(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename='client.log',
        filemode='w')

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    sh.setFormatter(formatter)
    logging.getLogger('').addHandler(sh)


def register_options():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-i", "--host", dest="host",
                      default="192.168.1.156", help="specify host, default is 192.168.1.156")
    parser.add_option("-p", "--port", dest="port",
                      type="int",
                      default=3050, help="specify port, default is 58849")
    parser.add_option("-n", "--num", dest="num",
                      type="int",
                      default=1, help="specify threads num, default is 1")
    parser.add_option("-d", "--daemon", dest="daemon",
                      action='store_true',
                      default=False, help="set daemon process, default is false")

    (options, args) = parser.parse_args()
    return options


def stop_threads():
    for th in THREADS:
        th.stop()
        # logging.info('stop %s ...' % th.getName())
    global STOP
    STOP = True


def sig_handler(sig, frame):
    stop_threads()


def verify_data(data):
    pass
    if len(data) < 24:
        logging.error('received data length less than 24')

    parts = struct.unpack("6I", data[0:24])
    parts = [str(socket.ntohl(x)) for x in parts]
    header = ', '.join(parts)
    body = ''
    try:
        body = json.loads(data[24:])
        print header
        print body
    except:
        logging.error('received data body is not JSON string')
        return ''

    logging.debug('header:%s body:%s' % (header, json.dumps(body, indent=4)))

    try:
        if parts[2] is 90011:
            logging.info('receive data %d: %s' % parts[2], body)

        if parts[2] is 90012:
            logging.info('receive data %d: %d' % parts[2], body)

        if parts[2] is 90013:
            logging.info('receive data %d: %d' % parts[2], body)
    except:
        logging.error('data in body is not JSON string')


class Client(threading.Thread):
    clients = set()

    def __init__(self, ip, port):
        Client.clients.add(self)
        threading.Thread.__init__(self)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._address = (ip, port)
        self.thread_stop = False
        logging.info('new connection %d to %s:%d' % (len(Client.clients), self._address[0], self._address[1]))

    def run(self):
        try:
            self._sock.connect(self._address)
        except socket.error, arg:
            (errno, err_msg) = arg
            logging.error('connect server failed: %s, errno=%d' % (err_msg, errno))
            return

        self.rec_data()
        # self.send()

    def send(self, to_uid):

        # body = {"touid": to_uid}
        # json_arr = json.dumps(body)
        # orig = [17, 100, 90003, 65536, len(json_arr), 520]

        body = {"touid": to_uid, "message": "hello world", "type": 1}
        json_arr = json.dumps(body)
        orig = [17, 100, 90001, 65536, len(json_arr), 520]

        elems = [socket.htonl(x) for x in orig]
        header = pack('6I', elems[0], elems[1], elems[2],
                      elems[3], elems[4], elems[5])
        msg = header + json_arr
        # msg = header
        print json_arr, header
        try:
            self._sock.send(msg)
        except socket.error, arg:
            (errno, err_msg) = arg
            logging.error('send msg to server failed: %s, errno=%d' % (err_msg, errno))
            stop_threads()
            return

        header_str = ', '.join([str(x) for x in orig])
        logging.debug('send header: (%d : %s) to %s:%d' % (len(header), header_str,
                                                           self._address[0], self._address[1]))
        logging.debug('send body: (%d : %s) to %s:%d' % (len(body), body,
                                                         self._address[0], self._address[1]))

    def stop(self):
        self.thread_stop = True

    def rec_data(self):
        self._sock.setblocking(0)
        recv_buf = ''
        while True:
            time.sleep(0.1)
            try:
                recv_buf = self._sock.recv(4096)
                if len(recv_buf) >= 24:
                    print len(recv_buf)
                    verify_data(recv_buf)
            except Exception, e:
                pass
                # logging.error('recv data error %s' % e)


if __name__ == '__main__':

    init_log()
    opts = register_options()

    logging.info('start %d threads to server %s:%d ...' % (opts.num, opts.host, opts.port))

    for i in xrange(opts.num):
        client = Client(opts.host, opts.port)
        THREADS.append(client)

    for i in THREADS:
        # i.setDaemon(opts.daemon)
        i.start()

    """ register control+c kill thread
    """
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # while True:
    input_text = raw_input("Input Fun Num >>>> ")
        # if input_text.isdigit():
    THREADS[0].send("60HNr67d")
        # elif "quit" == input_text.lower() or "exit" == input_text.lower():
        #     exit(0)

    # master thread to catch signal
    while not STOP:
        time.sleep(0.01)

    # for i in range(len(THREADS)):
    #     THREADS[i].join()

    logging.info('stop ...')

