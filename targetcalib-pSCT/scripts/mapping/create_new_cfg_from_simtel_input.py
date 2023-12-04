"""
Get the X and Y coordinates from ctapipe by matching between rows and columns
between the ctapipe camera configuration and the target_calib Mapping
rows and columns
"""

import numpy as np
from ctapipe.instrument.camera import _get_min_pixel_seperation
from target_calib import CameraConfiguration
import pandas as pd
from IPython import embed


def main():
    camera_version = "1.1.0"
    camera_config = CameraConfiguration(camera_version)
    m = camera_config.GetMapping()
    mrows = np.array(m.GetRowVector())
    mcols = np.array(m.GetColumnVector())

    df_old = pd.read_csv(m.GetCfgPath(), sep='\t')

    df_simtel = pd.read_csv(
        "/Users/Jason/Downloads/camera_CHEC-S_prototype_26042018.dat",
        sep=' |\t', skiprows=36, skipfooter=513, engine='python', header=None,
        names=['Pixel', 'ipix', 'type', 'xpix', 'ypix', 'imod',
               'iboard', 'itmpix', 'id', 'on']
    )

    x_pix = df_simtel['xpix'].values
    y_pix = df_simtel['ypix'].values

    gx = np.histogram2d(x_pix, y_pix, weights=x_pix, bins=[53, 53])[0]
    gy = np.histogram2d(x_pix, y_pix, weights=y_pix, bins=[53, 53])[0]
    i = np.bincount(gx.nonzero()[0]).argmax()
    j = np.bincount(gy.nonzero()[0]).argmax()
    xc = gx[:, i][gx[:, i].nonzero()]
    yc = gy[j, :][gy[j, :].nonzero()]

    dist = _get_min_pixel_seperation(xc, yc)
    edges_x = np.zeros(xc.size + 1)
    edges_x[0:xc.size] = xc - dist / 2
    edges_x[-1] = xc[-1] + dist / 2
    edges_y = np.zeros(yc.size + 1)
    edges_y[0:yc.size] = yc - dist / 2
    edges_y[-1] = yc[-1] + dist / 2

    c_x = np.histogram2d(-y_pix, x_pix, bins=[-edges_y[::-1], edges_x],
                         weights=x_pix)[0]
    c_y = np.histogram2d(-y_pix, x_pix, bins=[-edges_y[::-1], edges_x],
                         weights=y_pix)[0]

    x = c_x[47 - mrows, mcols]
    y = c_y[47 - mrows, mcols]

    mx = x[:64] - x[:64].mean()
    my = y[:64] - y[:64].mean()

    df_old['xpix'] = x * 10**-2
    df_old['ypix'] = y * 10**-2

    df_old.to_csv("new_mapping.cfg", sep='\t', float_format='%.7f', index=False)


if __name__ == '__main__':
    main()
