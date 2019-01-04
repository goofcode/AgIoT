import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

import os

n = 16
cell_width = 10
cell_height = 10
total_cell = 256


def _get_pos(idx):
    r_start = int(idx / n) * cell_height
    r_end = r_start + cell_height
    c_start = int(idx % n) * cell_width
    c_end = c_start + cell_width

    return r_start, r_end, c_start, c_end


def _get_cell(img, idx):
    r_start, r_end, c_start, c_end = _get_pos(idx)
    return img[r_start:r_end, c_start:c_end]


def get_all_cells(img):
    return [(i, _get_cell(img, i)) for i in range(total_cell)]


def _get_SSIM(img1, img2):
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


def _get_man(img1, img2):
    img1 = img1.flatten()
    img2 = img2.flatten()
    return (np.abs(img1 - img2)).sum()


def _get_cos(img1, img2):
    img1 = img1.flatten()
    img2 = img2.flatten()

    img1 = img1 / np.linalg.norm(img1)
    img2 = img2 / np.linalg.norm(img2)

    return (1 - np.dot(img1, img2)) / 2


def _get_eucl(img1, img2):
    # type: (np.ndarray, np.ndarray) -> float

    flat1 = img1.flatten()
    flat2 = img2.flatten()

    return np.math.sqrt(((flat1 - flat2) ** 2).sum())


def _get_DSSIM(img1, img2):
    return (1 - _get_SSIM(img1, img2)) / 2


def _update_prev(i, update, cell):
    r_start, r_end, c_start, c_end = _get_pos(i)
    update[r_start:r_end, c_start: c_end] = cell


def _save(name, img):
    pil = Image.fromarray(img)
    pil.save('img/' + name + '.png')

with open('out/prev', 'rb') as f:
    img = f.read()
    prev = np.array(list(img)).reshape((160,160)).astype(np.uint8)

with open('out/now', 'rb') as f:
    img = f.read()
    now = np.array(list(img)).reshape((160,160)).astype(np.uint8)

man = np.copy(prev)
cos = np.copy(prev)
euc = np.copy(prev)
dssim = np.copy(prev)

man_thresh = 10000
cos_thresh = 0.001
eucl_thresh = 12
dssim_thresh = 0.067

counts = [0, 0, 0, 0]

for idx in range(total_cell):

    pcell = _get_cell(prev, idx)
    ncell = _get_cell(now, idx)

    man_diff = _get_man(pcell, ncell)
    if man_diff > man_thresh:
        _update_prev(idx, man, ncell)
        counts[0] += 1

    cos_diff = _get_cos(pcell, ncell)
    if cos_diff > cos_thresh:
        _update_prev(idx, cos, ncell)
        counts[1] += 1

    euc_diff = _get_eucl(pcell, ncell)
    if euc_diff > eucl_thresh:
        _update_prev(idx, euc, ncell)
        counts[2] += 1

    dssim_diff = _get_DSSIM(pcell, ncell)
    if dssim_diff > dssim_thresh:
        _update_prev(idx, dssim, ncell)
        counts[3] += 1

    print('{}\t{}\t{}\t{}'.format(man_diff, cos_diff, euc_diff, dssim_diff))

print(counts)

_save('prev', prev)
_save('now', now)
_save('man', man)
_save('cos', cos)
_save('euc', euc)
_save('dssim', dssim)

# for file in os.listdir('out'):
#     filename = 'out/' + file
#
    # with open(filename, 'rb') as f:
    #     img = f.read()
    #     img = np.array(list(img)).reshape((160,160))
    #     plt.imshow(img, cmap=plt.get_cmap('gray'))
    #     plt.title(file)
    #     plt.savefig('img/' + file + '.png')
    #     arr = np.array(list(img)).reshape((160,160)).astype(np.uint8)
    #     pil = Image.fromarray(arr)
    #     pil.save('img/' + file + '.png')