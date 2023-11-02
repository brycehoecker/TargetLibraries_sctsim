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

    def mask(self, image):
        image[0:8, 40:48] = np.ma.masked
        image[0:8, 0:8] = np.ma.masked
        image[40:48, 0:8] = np.ma.masked
        image[40:48, 40:48] = np.ma.masked

    def plot(self, values, title):
        image = np.ma.zeros((self.nrows, self.ncols))
        image[self.row, self.col] = values
        ml = self.nrows / 6
        self.mask(image)

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


class ImageSP(Image):
    def mask(self, image):
        image[0:4, 20:24] = np.ma.masked
        image[0:4, 0:4] = np.ma.masked
        image[20:24, 0:4] = np.ma.masked
        image[20:24, 20:24] = np.ma.masked


def main():
    c = CameraConfiguration("1.0.1")
    m = c.GetMapping()
    msp = m.GetMappingSP()

    poi_p = 35
    n_pixels = m.GetNPixels()
    row_p = np.array(m.GetRowVector())
    col_p = np.array(m.GetColumnVector())
    nei_p = np.zeros(n_pixels)
    single_p = np.zeros(n_pixels)
    nei_diag_p = np.zeros(n_pixels)
    single_diag_p = np.zeros(n_pixels)
    for p in range(n_pixels):
        nei = np.array(m.GetNeighbours(p))
        nei_diag = np.array(m.GetNeighbours(p, True))
        # nei_p[nei] += 1
        nei_p[p] += nei.size
        # nei_diag_p[nei_diag] += 1
        nei_diag_p[p] += nei_diag.size
        if p == poi_p:
            single_p[nei] += 1
            single_p[p] += 5
            single_diag_p[nei_diag] += 1
            single_diag_p[p] += 5

    poi_sp = 13
    n_sp = msp.GetNSuperPixels()
    row_sp = np.array(msp.GetRowVector())
    col_sp = np.array(msp.GetColumnVector())
    nei_sp = np.zeros(n_sp)
    single_sp = np.zeros(n_sp)
    nei_diag_sp = np.zeros(n_sp)
    single_diag_sp = np.zeros(n_sp)
    for p in range(n_sp):
        nei = np.array(msp.GetNeighbours(p))
        nei_diag = np.array(msp.GetNeighbours(p, True))
        # nei_sp[nei] += 1
        nei_sp[p] += nei.size
        # nei_diag_sp[nei_diag] += 1
        nei_diag_sp[p] += nei_diag.size
        if p == poi_sp:
            single_sp[nei] += 1
            single_sp[p] += 5
            single_diag_sp[nei_diag] += 1
            single_diag_sp[p] += 5

    p_nei_p = Image(row_p, col_p)
    p_nei_p.plot(nei_p, "Pixel Neighbour Tally")
    p_nei_p.add_text(nei_p)
    p_nei_p.save("nei_pixel_tally")

    p_nei_sp = ImageSP(row_sp, col_sp)
    p_nei_sp.plot(nei_sp, "SuperPixel Neighbour Tally")
    p_nei_sp.add_text(nei_sp)
    p_nei_sp.save("nei_superpixel_tally")

    p_single_p = Image(row_p, col_p)
    p_single_p.plot(single_p, "Pixel Neighbours")
    p_single_p.add_text(single_p)
    p_single_p.save("nei_pixel")

    p_single_sp = ImageSP(row_sp, col_sp)
    p_single_sp.plot(single_sp, "SuperPixel Neighbours")
    p_single_sp.add_text(single_sp)
    p_single_sp.save("nei_superpixel")

    # Diagonals

    p_nei_p = Image(row_p, col_p)
    p_nei_p.plot(nei_diag_p, "Pixel Neighbour Tally (Diagonal)")
    p_nei_p.add_text(nei_diag_p)
    p_nei_p.save("nei_diag_pixel_tally")

    p_nei_sp = ImageSP(row_sp, col_sp)
    p_nei_sp.plot(nei_diag_sp, "SuperPixel Neighbour Tally (Diagonal)")
    p_nei_sp.add_text(nei_diag_sp)
    p_nei_sp.save("nei_diag_superpixel_tally")

    p_single_p = Image(row_p, col_p)
    p_single_p.plot(single_diag_p, "Pixel Neighbours (Diagonal)")
    p_single_p.add_text(single_diag_p)
    p_single_p.save("nei_diag_pixel")

    p_single_sp = ImageSP(row_sp, col_sp)
    p_single_sp.plot(single_diag_sp, "SuperPixel Neighbours (Diagonal)")
    p_single_sp.add_text(single_diag_sp)
    p_single_sp.save("nei_diag_superpixel")


if __name__ == '__main__':
    main()
