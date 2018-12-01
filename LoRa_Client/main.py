import numpy as np
import picamera
import time
import serial
import sys

camera_ready_sleep = 4

sleep_period = 0.5
intercell_sleep = 0.1

thresholds = [100, 100, 0.5]    # manhattan, euclidean, cosine


class AtoI:

    def __init__(self, width, height, n, diff_alg):
        self._camera = picamera.PiCamera(resolution=(width, height))
        time.sleep(camera_ready_sleep)
        print("pi camera setup finished")
        sys.stdout.flush()

        self._lora_serial = serial.Serial('/dev/ttyUSB0', baudrate=115200)
        print(self._lora_serial.read_until()[:-1])
        sys.stdout.flush()

        self.n = n
        self.total_cell = n * n

        self.width = width
        self.height = height
        self.cell_width = int(width / self.n)
        self.cell_height = int(height / self.n)

        self._capture = np.empty(shape=(height * width * 3), dtype=np.uint8)
        self.now = None
        self.prev = None

        self.re_tx = 2
        self.ack_wait = 30

        self.diff_alg = diff_alg
        self.threshold = thresholds[diff_alg]

    def capture_gray_2d(self):
        self._camera.capture(self._capture, 'rgb')
        self.now = np.dot(np.reshape(self._capture, (self.height, self.width, 3)), [0.299, 0.587, 0.114]).astype(np.uint8)

        if self.prev is None:
            self.prev = np.copy(self.now)

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
        return self._send(bytearray(payload))

    def send_all_cells(self):
        for (idx, cell) in self.get_all_now_cells():
            print(self.send_cell(idx, cell))
            sys.stdout.flush()

            time.sleep(intercell_sleep)

    def _save(self):
        print('saving picture')
        sys.stdout.flush()

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

            if self._get_diff(pcell, ncell) > self.threshold:
                self.send_cell(idx, ncell)
                self._update_prev(idx, ncell)


if __name__ == "__main__":

    atoi = AtoI(160, 160, 16, 0)

    atoi.capture_gray_2d()
    atoi.send_all_cells()

    while True:

        atoi.capture_gray_2d()
        atoi.send_diff_and_update()
        time.sleep(sleep_period)
