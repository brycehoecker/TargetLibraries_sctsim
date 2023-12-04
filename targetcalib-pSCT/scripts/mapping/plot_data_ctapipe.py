"""
Plot data using TargetCalib and ctapipe
"""
import numpy as np
from matplotlib import pyplot as plt
from target_calib import MappingCHEC
from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay
from astropy import units as u


def main():

    m = MappingCHEC()
    # m.Rotate(3)

    xpix = np.array(m.GetXPixVector())
    ypix = np.array(m.GetYPixVector())

    pos = np.vstack([xpix, ypix]) * u.m
    foclen = 2.283 * u.m
    geom = CameraGeometry.guess(*pos, foclen)

    data = np.loadtxt("input_data.txt")

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)

    camera = CameraDisplay(geom, ax=ax, image=data, cmap='viridis')
    camera.add_colorbar()

    axl = m.fOTUpX_l+0.01
    ayl = m.fOTUpY_l
    adx = m.fOTUpX_u - axl+0.01
    ady = m.fOTUpY_u - ayl
    ax.arrow(axl, ayl+0.01, adx, ady, head_width=0.01, head_length=0.01,
             fc='r', ec='r')
    text = "ON-Telescope UP"
    ax.text(axl, ayl, text, fontsize=8, color='r', ha='center', va='bottom')

    fn = "image_p_plot_data_ctapipe.pdf"
    fig.savefig(fn, bbox_inches='tight')
    print("Figure created: {}".format(fn))


if __name__ == '__main__':
    main()
