import logging
import time

import numpy as np
import picamera
import serial

camera_ready_sleep = 4

sleep_period = 0.5
intercell_sleep = 0.1

thresholds = [100, 100, 0.5]  # manhattan, euclidean, cosine


class AtoI:

    def __init__(self, width, height, n, diff_alg, re_tx, wait):

        # ready logging
        self.logger = logging.getLogger('atoi')
        self.logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter("[%(asctime)s] %(message)s")

        file_handler = logging.FileHandler('lora.log')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)

        self.logger.debug('=' * 50)
        self.logger.debug('{}*{}, n:{}, diff:{}, re_tx:{}, ack_wait:{}'
                          .format(width, height, n, diff_alg, re_tx, wait*100))

        # ready camera
        self._camera = picamera.PiCamera(resolution=(width, height))
        time.sleep(camera_ready_sleep)
        self._camera.color_effects = (128, 128)
        self.logger.debug("pi camera setup finished")

        # ready lora
        self._lora_serial = serial.Serial('/dev/ttyUSB0', baudrate=115200)
        self.logger.debug(self._lora_serial.read_until()[:-1])

        self.n = n
        self.total_cell = n * n
        self.width = width
        self.height = height
        self.cell_width = int(width / self.n)
        self.cell_height = int(height / self.n)

        self._capture = np.empty(shape=(height * width * 3), dtype=np.uint8)
        self.now = None
        self.prev = None

        self.re_tx = re_tx
        self.ack_wait = wait

        self.diff_alg = diff_alg
        self.threshold = thresholds[diff_alg]

        self.logger.debug("initialization finished")

    def capture_gray_2d(self):

        self._camera.capture(self._capture, 'rgb')
        self.now = np.array([self._capture[i*3] for i in range(160*160)]).reshape(160, 160)

        if self.prev is None:
            self.prev = np.copy(self.now)

        self.logger.debug('capture')

        self._save()

    def _send(self, payload, ack=True):
        # type: (bytearray, bool) -> int
        self._lora_serial.write(chr(len(payload)))
        self._lora_serial.write(payload)

        if not ack:
            self._lora_serial.write('s')
        else:
            self._lora_serial.write('a')
            self._lora_serial.write(chr(self.re_tx))
            self._lora_serial.write(chr(self.ack_wait))

        return int(self._lora_serial.readline())

    def _get_pos(self, idx):
        r_start = int(idx / self.n) * self.cell_height
        r_end = r_start + self.cell_height
        c_start = int(idx % self.n) * self.cell_width
        c_end = c_start + self.cell_width

        return r_start, r_end, c_start, c_end

    def _get_cell(self, img, idx):
        r_start, r_end, c_start, c_end = self._get_pos(idx)
        return img[r_start:r_end, c_start:c_end]

    def get_now_cell(self, idx):
        return self._get_cell(self.now, idx)

    def get_prev_cell(self, idx):
        return self._get_cell(self.prev, idx)

    def get_all_now_cells(self):
        # type: () -> [(int, np.ndarray)]
        return [(i, self.get_now_cell(i)) for i in range(self.total_cell)]

    def send_cell(self, idx, cell):
        # type: (int, np.ndarray) -> int
        payload = [idx]
        payload.extend(cell.astype(np.uint8).reshape(self.cell_width * self.cell_height).tolist())

        start_time = time.time()
        sent = self._send(bytearray(payload))
        self.logger.debug('cell\t{}\t{}\t{},'.format(idx, sent, time.time() - start_time))
        return sent

    def send_all_cells(self):

        for (idx, cell) in self.get_all_now_cells():
            self.send_cell(idx, cell)
            time.sleep(intercell_sleep)

    def _save(self):
        with open('output', 'wb') as f:
            f.write(self.now)

    def _get_diff(self, pcell, ncell):

        pcell = pcell.flatten()
        ncell = ncell.flatten()

        # euclidean distance
        if self.diff_alg == 0:
            return ((ncell - pcell) ** 2).sum()

        # manhattan distance
        elif self.diff_alg == 1:
            return (np.abs(ncell - pcell)).sum()

        # cosine distance
        elif self.diff_alg == 2:
            pcell = pcell / np.linalg.norm(pcell)
            ncell = ncell / np.linalg.norm(ncell)
            return np.dot(pcell, ncell)

    def _update_prev(self, idx, cell):
        r_start, r_end, c_start, c_end = self._get_pos(idx)
        self.prev[r_start:r_end, c_start: c_end] = cell

    def send_diff_and_update(self):

        for idx in range(self.total_cell):

            pcell = self.get_prev_cell(idx)
            ncell = self.get_now_cell(idx)

            diff = self._get_diff(pcell, ncell)
            self.logger.debug('diff\t{}\t{}\t{}'.format(idx, diff, self.threshold))

            if diff > self.threshold:
                self.send_cell(idx, ncell)
                self._update_prev(idx, ncell)


if __name__ == "__main__":

    atoi = AtoI(160, 160, 16, 0, 2, 30)

    atoi.capture_gray_2d()
    atoi.send_all_cells()

    while True:
        atoi.capture_gray_2d()
        atoi.send_diff_and_update()
        time.sleep(sleep_period)
