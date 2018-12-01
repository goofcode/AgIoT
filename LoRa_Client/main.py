import numpy as np
import picamera
import time
import serial

threshold = 100
sleep_period = 0.5
intercell_sleep = 0.1


class AtoI:

    def __init__(self, width, height, n):
        self._camera = picamera.PiCamera(resolution=(width, height))
        time.sleep(2)
        print("pi camera setup finished")
        self._lora_serial = serial.Serial('/dev/ttyUSB0', baudrate=115200)
        print(self._lora_serial.read_until())
        self._capture = np.empty(shape=(height * width * 3), dtype=np.uint8)

        self.n = n
        self.total_cell = n * n

        self.width = width
        self.height = height
        self.cell_width = int(width / self.n)
        self.cell_height = int(height / self.n)

        self.now = None
        self.prev = None

        self.re_tx = 2
        self.ack_wait = 30

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
        r_start = int(idx % self.n) * self.cell_height
        r_end = r_start + self.cell_height
        c_start = int(idx / self.n) * self.cell_width
        c_end = c_start + self.cell_width

        return r_start, r_end, c_start, c_end

    def get_cell(self, img, idx):
        r_start, r_end, c_start, c_end = self._get_pos(idx)
        return img[r_start:r_end, c_start:c_end]

    def get_all_cells(self, img):
        return [(i, self.get_cell(img, i)) for i in range(self.total_cell)]

    def update_prev(self, idx):
        r_start, r_end, c_start, c_end = self._get_pos(idx)
        self.prev[r_start:r_end, c_start: c_end] = self.now[r_start:r_end, c_start: c_end]

    def _get_diff(self, idx):
        return ((self.get_cell(self.now, idx) - self.get_cell(self.prev, idx)) ** 2).mean()

    def get_diff_cells(self):

        diff_cells = []

        for idx in range(self.total_cell):
            if self._get_diff(idx) > threshold:
                diff_cells.append((idx, self.get_cell(self.now, idx)))

        return diff_cells

    # def send_meta(self):
    #     payload = [type_meta, self.img_id, self.total_cell]
    #     return self._send(bytearray(payload), True)

    def send_cell(self, idx, cell):
        # type: (int, np.ndarray) -> int
        payload = [idx]
        payload.extend(cell.astype(np.uint8).reshape(self.cell_width * self.cell_height).tolist())
        return self._send(bytearray(payload))

    def send_all_cells(self):
        for (idx, cell) in self.get_all_cells(self.now):
            print(self.send_cell(idx, cell))
            time.sleep(intercell_sleep)

    def _send(self, payload):
        # type: (bytearray, bool) -> int

        self._lora_serial.write(chr(len(payload)))
        self._lora_serial.write(payload)
        return int(self._lora_serial.readline())

    def save(self):
        print('saving picture')
        with open('output', 'w') as f:
            f.writelines(', '.join(str(item) for item in row) + '\n' for row in self.now )


if __name__ == "__main__":

    # atoi = AtoI(160, 160, 10)
    #
    # atoi.capture_gray_2d()
    # atoi.send_all_cells()
    #
    # time.sleep(sleep_period)
    #
    # while True:
    #
    #     atoi.capture_gray_2d()
    #
    #     for diff_cell in atoi.get_diff_cells():
    #         atoi.send_cell(diff_cell['idx'], diff_cell['cell'])
    #         atoi.update_prev(diff_cell['idx'], diff_cell['cell'])
    #
    #     time.sleep(sleep_period)

    atoi = AtoI(160, 160, 16)

    atoi.capture_gray_2d()
    atoi.save()

    while True:
        atoi.send_all_cells()
        time.sleep(sleep_period)
