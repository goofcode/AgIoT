import numpy as np
import matplotlib.pyplot as plt

with open('output', 'rb') as f:
    img = f.read()

img = np.array(list(img))

print (img.shape)
img = np.reshape(img, (100,100))

print(img)

plt.imshow(img, cmap=plt.get_cmap('gray'))
plt.show()