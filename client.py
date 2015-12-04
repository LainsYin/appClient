#!/usr/bin/env python2.7
# -*-coding:utf-8 -*-

import sys
import time
import socket
import signal
import json
import struct
import logging
import ConfigParser
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
                      default=3050, help="specify port, default is 3050")
    parser.add_option("-f", "--fun", dest="fun",
                      type="int",
                      default=90001, help="specify function num, default is 90001")
    parser.add_option("-n", "--num", dest="num",
                      type="int",
                      default=1, help="specify threads num, default is 1")

    parser.add_option("-d", "--daemon", dest="daemon",
                      action='store_true',
                      default=True, help="set daemon process, default is true")

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

    logging.info('received data :  header:%s ' % header)
    logging.info('received data :  body:%s' % data[24:])


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

    def send(self, header, body):

        orig = header
        assert isinstance(orig, object)
        orig[4] = len(body)

        elems = [socket.htonl(x) for x in orig]
        header_net = pack('6I', elems[0], elems[1], elems[2],
                      elems[3], elems[4], elems[5])
        msg = header_net + body
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
        while True:
            time.sleep(0.1)
            try:
                rec_buf = self._sock.recv(4096)
                if len(rec_buf) >= 24:
                    verify_data(rec_buf)
            except :
                pass
                # logging.error('recv data error %s' % e)


if __name__ == '__main__':

    init_log()
    opts = register_options()
    logging.info('start %d threads to server %s:%d ...' % (opts.num, opts.host, opts.port))

    conf = ConfigParser.ConfigParser()
    conf.read("./config.ini")
    fun_num = opts.fun
    try:
        header_str = conf.get("%s" % fun_num, "header").split(",")
        body = conf.get("%s" % fun_num, "body")
        header = [int(x) for x in header_str]
    except Exception, e:
        logging.info(e)
        exit(1)

    for i in xrange(opts.num):
        client = Client(opts.host, opts.port)
        THREADS.append(client)

    for i in THREADS:
        i.setDaemon(opts.daemon)
        i.start()

    """ register control+c kill thread
    """
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    logging.info("Waiting for 1 second")
    time.sleep(1)
    THREADS[0].send(header, body)

# master thread to catch signal
    while not STOP:
        time.sleep(0.01)

    logging.info('stop ...')

