"""
Plot data using just TargetCalib and python
"""
import numpy as np
from matplotlib import pyplot as plt
from target_calib import CameraConfiguration


def main():

    camera_version = "1.0.1"
    camera_config = CameraConfiguration(camera_version)
    m = camera_config.GetMapping()

    row = np.array(m.GetRowVector())
    col = np.array(m.GetColumnVector())
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

    axl = m.fOTUpCol_l
    ayl = m.fOTUpRow_l
    adx = m.fOTUpCol_u - axl
    ady = m.fOTUpRow_u - ayl
    ax.arrow(axl, ayl, adx, ady, head_width=1, head_length=1, fc='r', ec='r')
    text = "ON-Telescope UP"
    ax.text(axl, ayl, text, fontsize=8, color='r', ha='center', va='bottom')

    fn = "image_p_plot_data_tc.pdf"
    fig.savefig(fn, bbox_inches='tight')
    print("Figure created: {}".format(fn))


if __name__ == '__main__':
    main()
