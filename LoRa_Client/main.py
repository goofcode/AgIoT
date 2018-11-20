import numpy as np
import picamera
import time

n = 10
total_cell = n ** 2
width = 160
height = 160

threshold = 100
sleep_period = 0.5
intercell_sleep = 0.01


def mse(cell1, cell2):
    return ((cell1 - cell2) ** 2).mean()


class AtoI:

    def __init__(self):
        self._camera = picamera.PiCamera()
        self._capture = np.empty(shape=(height * width * 3), dtype=np.uint8)
        self.now = None
        self.prev = None

    @staticmethod
    def get_cell_pos(idx):
        return int(idx / n) * n, int(idx % n) * n

    @staticmethod
    def get_all_cells(img):
        all_cell = []

        for i in range(total_cell):
            row, col = AtoI.get_cell_pos(i)
            all_cell.append(img[row: row + n, col:col + n])

        return all_cell

    def capture_gray_2d(self):
        self._camera.capture(self._capture, 'rgb')
        self.now = np.dot(np.reshape(self._capture, (height, width, 3)), [0.299, 0.587, 0.114])

        if self.prev is None:
            self.prev = np.copy(self.now)

    def update_prev(self, idx, cell):
        row, col = AtoI.get_cell_pos(idx)
        self.prev[row: row + n, col: col + n] = cell

    def get_diff_cells(self):

        now_cells = AtoI.get_all_cells(self.now)
        prev_cells = AtoI.get_all_cells(self.prev)

        diff_cells = []

        for idx in range(total_cell):
            if mse(now_cells[idx], prev_cells[idx]) > threshold:
                diff_cells.append({"idx": idx, "cell": now_cells[idx]})

        return diff_cells

    def send_meta(self):
        pass

    def send_cell(self, idx, cell):
        pass

    def send_all_cells(self):
        for idx, cell in enumerate(AtoI.get_all_cells(self.now)):
            self.send_cell(idx, cell)
            time.sleep(intercell_sleep)


if __name__ == "__main__":

    atoi = AtoI()

    atoi.capture_gray_2d()
    atoi.send_meta()
    atoi.send_all_cells()

    time.sleep(sleep_period)

    while True:

        atoi.capture_gray_2d()

        for diff_cell in atoi.get_diff_cells():
            atoi.send_cell(diff_cell['idx'], diff_cell['cell'])
            atoi.update_prev(diff_cell['idx'], diff_cell['cell'])

        time.sleep(sleep_period)
