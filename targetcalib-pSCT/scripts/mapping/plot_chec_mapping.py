"""
Plot the pixel mapping created for CHEC-S inside TargetCalib
"""
import numpy as np
from matplotlib import pyplot as plt
from target_calib import CameraConfiguration


class Image:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.nrows = row.max() + 1
        self.ncols = col.max() + 1
        self.npix = row.size

        self.fig = None
        self.ax = None

    def plot(self, values, title):
        image = np.ma.zeros((self.nrows, self.ncols))
        image[self.row, self.col] = values
        image[0:8, 40:48] = np.ma.masked
        image[0:8, 0:8] = np.ma.masked
        image[40:48, 0:8] = np.ma.masked
        image[40:48, 40:48] = np.ma.masked

        self.fig = plt.figure(figsize=(10, 10))
        self.ax = self.fig.add_subplot(111)
        im = self.ax.imshow(image, origin='lower')
        self.fig.colorbar(im)
        self.fig.suptitle(title)

    def add_text(self, values, fmt=None, size=3):
        for pix in range(self.npix):
            pos_x = self.col[pix]
            pos_y = self.row[pix]
            val = values[pix]
            if fmt:
                val = fmt.format(val)
            self.ax.text(pos_x, pos_y, val, fontsize=size,
                         color='w', ha='center')

    def add_direction(self, axl, ayl, adx, ady):
        self.ax.arrow(axl, ayl, adx, ady, head_width=1, head_length=1,
                      fc='r', ec='r')
        text = "ON-Telescope UP"
        self.ax.text(axl, ayl, text, fontsize=8, color='r', ha='center',
                va='bottom')

    def save(self, fn):
        self.fig.savefig("{}.pdf".format(fn), bbox_inches='tight')
        print("Figure created: {}".format(fn))


def main():
    camera_version = "1.0.1"
    camera_config = CameraConfiguration(camera_version)
    m = camera_config.GetMapping()

    pixel = np.array(m.GetPixelVector())
    slot = np.array(m.GetSlotVector())
    asic = np.array(m.GetASICVector())
    ch = np.array(m.GetChannelVector())
    tmpix = np.array(m.GetTMPixelVector())
    row = np.array(m.GetRowVector())
    col = np.array(m.GetColumnVector())
    sipmpix = np.array(m.GetSipmPixVector())
    triggerpatch = np.array(m.GetTriggerPatchVector())
    hvpatch = np.array(m.GetHVPatchVector())
    sp = np.array(m.GetSuperPixelVector())
    x_coord = np.array(m.GetXPixVector())
    y_coord = np.array(m.GetYPixVector())

    axl = m.fOTUpCol_l
    ayl = m.fOTUpRow_l
    adx = m.fOTUpCol_u - axl
    ady = m.fOTUpRow_u - ayl

    charge = np.loadtxt("input_data.txt")

    image = Image(row, col)

    image.plot(pixel, "Pixel")
    image.add_text(pixel, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_pixel")

    image.plot(slot, "Slot")
    image.add_text(slot, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_slot")

    image.plot(asic, "ASIC")
    image.add_text(asic, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_asic")

    image.plot(ch, "CH")
    image.add_text(ch, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_ch")

    image.plot(tmpix, "TM Pixel")
    image.add_text(tmpix, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_tmpix")

    image.plot(row, "Row")
    image.add_text(row, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_row")

    image.plot(col, "Column")
    image.add_text(col, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_col")

    image.plot(sipmpix, "SiPM Pixel (Hamamatsu)")
    image.add_text(sipmpix, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_sipmpix")

    image.plot(triggerpatch, "Trigger SP Patch")
    image.add_text(triggerpatch, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_triggerpatch")

    image.plot(hvpatch, "HV SP Patch")
    image.add_text(hvpatch, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_hvpatch")

    image.plot(sp, "Superpixel")
    image.add_text(sp, size=3)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_sp")

    image.plot(x_coord, "X Coordinate")
    image.add_text(x_coord, "{:.4f}", size=2)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_x")

    image.plot(y_coord, "Y Coordinate")
    image.add_text(y_coord, "{:.4f}", size=2)
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_y")

    image.plot(charge, "Data")
    image.add_direction(axl, ayl, adx, ady)
    image.save("image_data")


if __name__ == '__main__':
    main()
