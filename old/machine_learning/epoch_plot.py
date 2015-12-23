#!/usr/bin/env python3
# SARbayes/machine_learning/epoch_plot.py


import matplotlib.pyplot as plt
import numpy as np


with open('epoch-error.txt') as data_file:
    error = np.fromiter((float(line) for line in data_file if line.strip()), 
        dtype=np.float64)

epoch = np.arange(0, len(error))

plt.title('Error vs. Epoch')
plt.xlabel('Epoch')
plt.ylabel(r'Error')

plt.plot(epoch, error)

plt.xlim(0, plt.xlim()[1])
plt.ylim(0, plt.ylim()[1])
plt.xticks(np.arange(0, plt.xlim()[1]//100*100 + 1, plt.xlim()[1]//5))
plt.yticks(np.arange(0, plt.ylim()[1]//100*100 + 1, plt.ylim()[1]//5))

# plt.text(2000, 200, 
#    r'$E = \frac{1}{2}\sum_{i}(actual_i - predicted_i)^2$', fontsize=20)
plt.show()
