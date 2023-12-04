"""
Create a plot of all the TFInputs in a file
"""
import sys
from os import environ
from os.path import join, dirname
from glob import glob
import re
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
import target_calib
from IPython import embed


def main():
    if len(sys.argv) > 1:
        list_of_files = sys.argv[1:]
    else:
        list_of_files = glob(join(environ['TC_CONFIG_PATH'], "*_tf.tcal"))

    for fp in list_of_files:
        pattern = join(dirname(fp), 'TFInput_File_(.+?)_(.+?).tcal')
        try:
            reg_exp = re.search(pattern, fp)
            sn = reg_exp.group(1)
        except AttributeError:
            print("Problem with Regular Expression, "
                  "{} does not match patten {}".format(fp, pattern))

        reader = target_calib.TFInputArrayReader(fp)
        tf = np.array(reader.GetTFInput())
        amplitudes = np.array(reader.GetAmplitude())

        tf_rs = np.reshape(tf, (np.product(tf.shape[:-1]), tf.shape[-1]))

        median = np.median(tf_rs, axis=0)
        diff = np.abs(tf_rs - median[None, :])
        points = np.argsort(np.max(diff, axis=1))[::-1][:1000]
        outliers = np.zeros(tf_rs.shape[0], dtype=np.bool)
        outliers[points] = 1
        tf_out = tf_rs[outliers]
        tf_good = tf_rs[~outliers]

        fig = plt.figure(figsize=(8, 4))
        ax = fig.add_subplot(1, 1, 1)

        amp_tile = np.tile(amplitudes, (tf_good.shape[0],1))
        x = amp_tile.T.ravel()
        y = tf_good.T.ravel()
        ax.hist2d(x, y, bins=100, norm=LogNorm())

        x = amplitudes
        y = tf_out.T
        ax.plot(x, y)

        ax.set_title(sn)
        ax.set_xlabel("mV")
        ax.set_ylabel("ADC")

        ax.set_xlim(-500, 2600)
        ax.set_ylim(-500, 4000)

        output_path = join(dirname(fp), "{}_tfinput.pdf".format(sn))
        fig.savefig(output_path, bbox_inches='tight')
        print("Figure saved to: {}".format(output_path))


if __name__ == '__main__':
    main()
