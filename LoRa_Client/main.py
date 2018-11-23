import numpy as np
import picamera
import time
import serial

threshold = 100
sleep_period = 0.5
intercell_sleep = 1


class AtoI:

    def __init__(self, width, height, n):
        self._camera = picamera.PiCamera(resolution=(width, height))
        print("pi camera setup finished")
        self._lora_serial = serial.Serial('/dev/ttyUSB0', baudrate=115200)
        print(self._lora_serial.read_until())
        self._capture = np.empty(shape=(height * width * 3), dtype=np.uint8)

        self.img_id = 10
        self.n = n
        self.total_cell = n ** 2

        self.width = width
        self.height = height
        self.cell_width = width / self.n
        self.cell_height = height / self.n

        self.now = None
        self.prev = None

    def get_cell_pos(self, idx):
        row_start = (idx / self.n) * self.cell_width
        col_start = (idx % self.n) * self.cell_height
        return row_start, col_start

    def get_all_cells(self, img):

        all_cell = []

        for i in range(self.total_cell):
            row, col = self.get_cell_pos(i)
            all_cell.append(img[row: row + self.cell_width, col:col + self.cell_height])

        return all_cell

    def capture_gray_2d(self):
        self._camera.capture(self._capture, 'rgb')
        self.now = np.dot(np.reshape(self._capture, (self.height, self.width, 3)), [0.299, 0.587, 0.114])

        if self.prev is None:
            self.prev = np.copy(self.now)

    def update_prev(self, idx, cell):
        row, col = self.get_cell_pos(idx)
        self.prev[row: row + self.cell_width, col: col + self.cell_height] = cell

    def _get_diff(self, cell1, cell2):
        return ((cell1 - cell2) ** 2).mean()

    def get_diff_cells(self):

        now_cells = self.get_all_cells(self.now)
        prev_cells = self.get_all_cells(self.prev)

        diff_cells = []

        for idx in range(self.total_cell):
            if self._get_diff(now_cells[idx], prev_cells[idx]) > threshold:
                diff_cells.append({"idx": idx, "cell": now_cells[idx]})

        return diff_cells

    def _send(self, payload):
        # type: (bytearray, bool) -> bool

        self._lora_serial.write(chr(len(payload)))
        self._lora_serial.write(payload)

        print(self._lora_serial.readline())

        return True

    # def send_meta(self):
    #     payload = [type_meta, self.img_id, self.total_cell]
    #     return self._send(bytearray(payload), True)

    def send_cell(self, idx, cell):
        # type: (int, np.ndarray) -> bool
        payload = [idx]
        payload.extend(cell.astype(np.uint8).flatten().tolist())

        return self._send(bytearray(payload))

    def send_all_cells(self):
        for idx, cell in enumerate(self.get_all_cells(self.now)):
            self.send_cell(idx, cell)
            time.sleep(intercell_sleep)


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

    while True:

        atoi.capture_gray_2d()
        atoi.send_all_cells()

        time.sleep(sleep_period)
