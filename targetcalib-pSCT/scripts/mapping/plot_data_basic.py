"""
Plot data using just TargetCalib and python
"""
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd


def main():

    df = pd.read_csv('full_camera_mapping.cfg', sep='\t')

    row = df['row']
    col = df['col']
    nrows = row.max() + 1
    ncols = col.max() + 1

    data = np.loadtxt("input_data.txt")

    image = np.ma.zeros((nrows, ncols))
    image[row, col] = data
    image[0:8, 40:48] = np.ma.masked
    image[0:8, 0:8] = np.ma.masked
    image[40:48, 0:8] = np.ma.masked
    image[40:48, 40:48] = np.ma.masked

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    im = ax.imshow(image, origin='lower')
    fig.colorbar(im)

    axl = 44
    ayl = 41
    adx = 0
    ady = 5
    ax.arrow(axl, ayl, adx, ady, head_width=1, head_length=1, fc='r', ec='r')
    text = "ON-Telescope UP"
    ax.text(axl, ayl, text, fontsize=8, color='r', ha='center', va='bottom')

    fn = "image_p_plot_data_basic.pdf"
    fig.savefig(fn, bbox_inches='tight')
    print("Figure created: {}".format(fn))


if __name__ == '__main__':
    main()
