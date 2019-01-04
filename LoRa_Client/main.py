import logging
import time
import datetime

import numpy as np
import picamera
import serial

camera_ready_sleep = 4

sleep_period = 0.5
intercell_sleep = 0.1

file_idx = 0

class AtoI:

    def __init__(self, width, height, n, diff_alg, re_tx, wait):

        # ready logging
        self.logger = logging.getLogger('atoi')
        self.logger.setLevel(logging.DEBUG)
        log_format = logging.Formatter("%(asctime)s\t%(message)s")

        file_handler = logging.FileHandler(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M') +'.log')
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        # console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        self.logger.debug('=' * 50)
        self.logger.info('{}*{}, n:{}, diff:{}, re_tx:{}, ack_wait:{}'
                          .format(width, height, n, diff_alg, re_tx, wait * 100))

        # ready camera
        self._camera = picamera.PiCamera(resolution=(width, height))
        time.sleep(camera_ready_sleep)
        self._camera.color_effects = (128, 128)
        self._camera.rotation = 180
        self.logger.info("pi camera setup finished")

        # ready lora
        self._lora_serial = serial.Serial('/dev/ttyUSB0', baudrate=115200)
        self.logger.info(self._lora_serial.read_until()[:-1])

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
        # self.threshold = self._get_default_threshold()
        self.threshold = 0.12
        self.margin = 0

        self.pending = False
        self.buffer = None

        self.logger.info('default threshold\t{}'.format(self.threshold))

        self.file_idx = 0

        self.logger.info("initialization finished")

    def _capture_np(self):
        self._camera.capture(self._capture, 'rgb')
        return np.array([self._capture[i * 3] for i in range(160 * 160)]).reshape(160, 160)

    def capture(self):

        self.now = self._capture_np()
        if self.prev is None:
            self.prev = np.copy(self.now)

        self.logger.info('capture')

        self._save()

    def _send(self, payload, ack=True):
        # type: (bytearray, bool) -> int

        if not self.pending:
            self.buffer = bytearray(payload)
            self.pending = True
            return -1

        else:
            self.buffer.extend(payload)

            self._lora_serial.write(chr(len(self.buffer)))
            self._lora_serial.write(self.buffer)

            # print((self._lora_serial.readline()))
            # print((self._lora_serial.readline()))

            if not ack:
                self._lora_serial.write('s')
            else:
                self._lora_serial.write('a')
                self._lora_serial.write(chr(self.re_tx))
                self._lora_serial.write(chr(self.ack_wait))

            self.pending = False

            return int(self._lora_serial.readline())

        # self._lora_serial.write(chr(12))
        # self._lora_serial.write(b"123456789012")
        #
        # if not ack:
        #     self._lora_serial.write('s')
        # else:
        #     self._lora_serial.write('a')
        #     self._lora_serial.write(chr(self.re_tx))
        #     self._lora_serial.write(chr(self.ack_wait))
        #
        # return int(self._lora_serial.readline())

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
        self.logger.debug('cell\t{}\t{}\t{:.2f}'.format(idx, sent, time.time() - start_time))
        return sent

    def send_all_cells(self):

        for (idx, cell) in self.get_all_now_cells():
            self.send_cell(idx, cell)
            time.sleep(intercell_sleep)

    def _save(self):
        with open('out/output' + str(self.file_idx), 'wb') as f:
            f.write(self.now)

        self.file_idx += 1

    def _get_SSIM(self, img1, img2):
        # type: (np.ndarray, np.ndarray) -> float

        flat1 = img1.flatten()
        flat2 = img2.flatten()

        m_x = flat1.mean()
        m_y = flat2.mean()
        dev_x = flat1.std()
        dev_y = flat2.std()

        dev_xy = np.dot(flat1 - m_x, flat2 - m_y).sum() / len(flat1)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        return ((2 * m_x * m_y + c1) * (2 * dev_xy + c2)) / (
                (m_x ** 2 + m_y ** 2 + c1) * (dev_x ** 2 + dev_y ** 2 + c2))

    def _get_MSE(self, img1, img2):
        # type: (np.ndarray, np.ndarray) -> float

        flat1 = img1.flatten()
        flat2 = img2.flatten()

        return ((flat2 - flat1)**2).mean()

    def _get_DSSIM(self, img1, img2):
        return (1 - self._get_SSIM(img1,img2))/2

    def _get_diff(self, pcell, ncell):
        # type: (np.ndarray, np.ndarray) -> float

        pcell = pcell.flatten().astype(np.float)
        ncell = ncell.flatten().astype(np.float)

        # euclidean distance
        if self.diff_alg == 0:
            return np.math.sqrt(((ncell - pcell) ** 2).sum())

        # DSSIM
        elif self.diff_alg == 1:
            return self._get_DSSIM(pcell, ncell)

    def _update_prev(self, idx, cell):
        r_start, r_end, c_start, c_end = self._get_pos(idx)
        self.prev[r_start:r_end, c_start: c_end] = cell

    def send_diff_and_update(self):

        diffs = []

        for idx in range(self.total_cell):

            pcell = self.get_prev_cell(idx)
            ncell = self.get_now_cell(idx)

            diff = self._get_diff(pcell, ncell)
            self.logger.debug('diff\t{}\t{:.3f}\t{:.3f}'.format(idx, diff, self.threshold + self.margin))

            diffs.append(diff)

            if diff > self.threshold + self.margin:
                self.send_cell(idx, ncell)
                self._update_prev(idx, ncell)

        # self.update_threshold(diffs)
        self.logger.info('image SSIM\t{:.5f}'.format(self._get_SSIM(self.prev, self.now)))
        self.logger.info('image MSE\t{:.5f}'.format(self._get_MSE(self.prev, self.now)))

    def _get_Tn(self, diffs):
        return sum(diffs) / len(diffs)

    def _get_default_threshold(self):

        first = self._capture_np()
        time.sleep(0.1)
        second = self._capture_np()

        diffs = []

        for idx in range(self.total_cell):
            fcell = self._get_cell(first, idx)
            scell = self._get_cell(second, idx)

            diffs.append(self._get_diff(fcell, scell))

        return self._get_Tn(diffs)

    def update_threshold(self, diffs):
        alpha = 0.05
        self.threshold = (1 - alpha) * self.threshold + alpha * self._get_Tn(diffs)
        self.logger.info('threshold\t{}'.format(self.threshold))


if __name__ == "__main__":

    atoi = AtoI(160, 160, n=16, diff_alg=1, re_tx=2, wait=30)

    atoi.capture()
    atoi.send_all_cells()

    while True:
        atoi.capture()
        atoi.send_diff_and_update()
        time.sleep(sleep_period)

