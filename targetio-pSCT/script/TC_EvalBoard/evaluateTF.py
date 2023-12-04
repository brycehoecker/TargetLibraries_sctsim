import pdb

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress


# outdir = "/home/cta/luigi/TC_EvalBoard/data/20160307/1VpedDAC_SBias1050/"
# infile = outdir+"TFdata.npz"

def DAC2mV(DAC_array):
    """
    based on measure performed by LT using TC eval board
    :param: array of DAC Vped values
    :return: array of Vped values in mV
    """
    mV_array = -2.76 + 0.611 * DAC_array
    return mV_array


class TargetTF:
    def __init__(self, infile):
        data = np.load(infile)
        try:
            self.tf_array = data['arr_0']
            if np.any(self.tf_array == 0):
                print "WARNING: the TF array contains 0 values"
            Vped_DAC = data['arr_1']
            self.Vped = DAC2mV(Vped_DAC)
            if not len(self.Vped) == len(self.tf_array):
                print "mismatch between array size in input file"
            self.nvped, self.nsample, self.nevent = np.shape(self.tf_array)
            self.tfs = np.average(self.tf_array, axis=2)
        except:
            print "failed to load TF data from input file"

    def plot_TF(self, outdir, xmin=0, xmax=-1):
        fig = plt.figure("Transfer Function")
        ax = plt.subplot(111)
        ax.set_xlabel("Vped (mV)", fontsize=14)
        ax.set_ylabel("ADC counts", fontsize=14)
        for cell in range(self.nsample):
            ax.plot(self.Vped, self.tfs[:, cell])
        plt.axvline(self.Vped[xmin], linestyle='--', color='b')
        plt.axvline(np.average(self.Vped[xmax]), linestyle='--', color='b')
        #plt.axvline(446.325, linestyle='--', color='b')
        #plt.axvline(2279.325, linestyle='--', color='b')
        fig.savefig(outdir + "TF.png")
        fig.clf()

    def plot_avgTF(self,outdir,xmin=0,xmax=-1):
        fig = plt.figure("Average Transfer Function")
        ax = plt.subplot(111)
        ax.set_xlabel("Input DC voltage (mV)", fontsize=14)
        ax.set_ylabel("ADC counts", fontsize=14)
        ax.set_ylim(200,4200)
        ax.grid(True)
        xmin=np.min(xmin.astype('int'))-1
        xmax=np.max(xmax.astype('int'))+1
        #print xmin, xmax
        ax.plot(self.Vped[xmin:xmax+1], np.average(self.tfs[xmin:xmax+1, :],axis=1),color='k')
        #plt.axvline(self.Vped[xmin], linestyle='--', color='b')
        #plt.axvline(np.average(self.Vped[xmax]), linestyle='--', color='b')
        #plt.axvline(446.325, linestyle='--', color='b')
        #plt.axvline(2279.325, linestyle='--', color='b')
        fig.savefig(outdir + "avgTF.png")
        fig.clf()

    def plot_DC_noise(self, outdir, noise_cut=4, xmin=0, xmax=-1, npoint=2):
        fig = plt.figure("DC noise")
        ax = plt.subplot(111)
        ax.set_xlabel("Vped (mV)", fontsize=14)
        ax.set_ylabel("RMS (mV)", fontsize=14)
        ax.set_ylim(0, 2*noise_cut)
        ax.grid(True)
        #ax.set_yscale('log')
        rmsADC = np.std(self.tf_array, axis=2)
        slopes = [
            [linregress(self.Vped[vped - npoint:vped + npoint + 1], self.tfs[vped - npoint:vped + npoint + 1, cell])[0]
             for cell in
             range(self.nsample)] for vped in range(npoint, self.nvped - npoint)]
        slopes = np.array(slopes)
        slopes[slopes < 0.1] = 0.1
        rmsmV = rmsADC[npoint:-npoint, :] / slopes - 0.1
        avg_noise = np.average(rmsmV, axis=1)
        std_noise = np.std(rmsmV, axis=1)
        ax.plot(self.Vped[npoint+2:-npoint], avg_noise[2:], color='k')
        ax.plot(self.Vped[npoint+2:-npoint], avg_noise[2:] + std_noise[2:], linestyle=':', color='k')
        ax.plot(self.Vped[npoint+2:-npoint], avg_noise[2:] - std_noise[2:], linestyle=':', color='k')
        goodrange = np.where(avg_noise < noise_cut)
        x1 = goodrange[0][0] + npoint
        xmin = np.maximum(xmin, x1)
        x2 = goodrange[0][-1] + npoint
        xmax = np.maximum(xmax, x2)-1
        plt.axvline(self.Vped[xmin - 1], linestyle='--', color='b')
        plt.axhline(0.8, linestyle='--', color='g')
        plt.axvline(np.average(self.Vped[xmax + 1]), linestyle='--', color='b')
        fig.savefig(outdir + "DCnoise.png")
        fig.clf()
        return xmin, xmax, rmsmV, rmsADC[npoint:-npoint, :]

    def plot_nonlinearity(self, outdir, bound=10, lindev_cut=400, xmin = 0, xmax =-1):

        if xmin == 0 and xmax==-1:
        # first pass, to evaluate dynamic range span
            lininterp = np.zeros(np.shape(self.tfs))
            for cell in range(self.nsample):
                slope, intercept, r_value, p_value, std_err = linregress(self.Vped[bound:-bound],
                                                                         self.tfs[bound:-bound, cell])
                lininterp[:, cell] = intercept + slope * self.Vped

            lindev = self.tfs - lininterp
            xmin = np.min([np.min(np.where(np.abs(lindev[:, cell]) < lindev_cut)) for cell in range(self.nsample)])
            xmax = [np.max(np.where(np.abs(lindev[:, cell]) < lindev_cut)) for cell in range(self.nsample)]
            x2 = [np.where(self.tfs[:, cell] == np.max(self.tfs[:, cell]))[0][0] for cell in range(self.nsample)]
            xmax = [np.maximum(xmax[cell], x2[cell]) for cell in range(self.nsample)]
            xmax = np.array(xmax)

        # second pass, now do linear fit and calculate non linearity over range above
        lininterp = np.zeros(np.shape(self.tfs))
        Vlininterp = np.zeros(np.shape(self.tfs))
        Vlindev = np.zeros(np.shape(self.tfs))
        for cell in range(self.nsample):
            slope, intercept, r_value, p_value, std_err = linregress(self.Vped[xmin:np.min(xmax)],
                                                                     self.tfs[xmin:np.min(xmax), cell])
            lininterp[:, cell] = intercept + slope * self.Vped
            Vlininterp[:,cell] = (self.tfs[:,cell]-intercept)/slope
            Vlindev[:,cell] = self.Vped - Vlininterp[:,cell]
        lindev = self.tfs - lininterp

        fig = plt.figure("Nonlinearity")
        ax = plt.subplot(111)
        ax.set_xlabel("Vped (mV)", fontsize=14)
        ax.set_ylabel("Deviation from linear fit (ADC counts)", fontsize=14)
        ax.set_ylim(-500, 500)
        for cell in range(self.nsample):
            ax.plot(self.Vped, lindev[:, cell])
        plt.axvline(self.Vped[xmin - 1], linestyle='--', color='k')
        plt.axvline(np.average(self.Vped[np.minimum(xmax + 1, len(self.Vped) - 1)]), linestyle='--', color='k')
        #plt.axvline(446.325, linestyle='--', color='b')
        #plt.axvline(2279.325, linestyle='--', color='b')
        fig.savefig(outdir + "Nonlinearity.png")
        fig.clf()

        lindev = np.abs(lindev)
        Vlindev = np.abs(Vlindev)
        INL = np.array([np.max(lindev[xmin:np.min(xmax), cell]) for cell in range(self.nsample)])
        INL = np.average(INL)
        INL_V = np.array([np.max(Vlindev[xmin:np.min(xmax), cell]) for cell in range(self.nsample)])
        INL_V = np.average(INL_V)

        return xmin, xmax, INL, INL_V

    def evaluate(self, outdir, npoint=2, noise_cut=6, lindev_cut=400):
        xmin, xmax, INL, INL_V = self.plot_nonlinearity(outdir,lindev_cut=lindev_cut)
        xmin, xmax, DC_noise, DC_noise_ADC = self.plot_DC_noise(outdir, xmin=xmin, xmax=xmax, npoint=npoint,
                                                                noise_cut=noise_cut)
        self.plot_TF(outdir, xmin=xmin-1, xmax=xmax+1)
        drange = np.average(self.Vped[xmax+1]-self.Vped[xmin-1])
        #print "dynamic range boundaries", np.average(self.Vped[xmin]), np.average(self.Vped[xmax]), "mV"
        print "dynamic range:", drange, "mV"
        drange_ADC = np.average(self.tfs[xmax+1] - self.tfs[xmin-1])
        print "dynamic range (ADC counts):", drange_ADC
        #recalculate INL in final range
        a, b, INL, INL_V = self.plot_nonlinearity(outdir,xmin=xmin,xmax=xmax)
        print "INL:", INL, "ADC counts,", INL_V, "mV"
        avdcnoise = np.average(DC_noise[xmin - npoint:np.min(xmax) - npoint, :])
        #print "DC noise", avdcnoise, "mV"
        dcnoise_optimal = np.average(np.min(DC_noise[xmin - npoint:np.min(xmax) - npoint, :],axis=1))
        #np.average(DC_noise[(self.Vped > 800) & (self.Vped < 1500)])
        print "DC noise (mV):", avdcnoise, "average", dcnoise_optimal, "optimal"
        # print "effective dynamic range", np.log2(drange/avdcnoise), "bits"
        # return drange, INL, avdcnoise, np.log2(drange/avdcnoise)
        avdcnoise_ADC = np.average(DC_noise_ADC[xmin - npoint:np.min(xmax) - npoint, :])
        #print "DC noise (ADC counts)", avdcnoise_ADC

        dcnoiseADC_optimal = np.average(np.min(DC_noise_ADC[xmin - npoint:np.min(xmax) - npoint, :],axis=1))
        #np.average(DC_noise[(self.Vped > 800) & (self.Vped < 1500)])
        print "DC noise (ADC counts):", avdcnoise_ADC, "average", dcnoiseADC_optimal, "(optimal)"
          # , "boundaries", np.average(self.tfs[xmin-npoint]) , np.average(self.tfs[np.min(xmax)-npoint:])
        # print xmin, self.Vped[xmin-1]
        dcnoise_lower = np.average(DC_noise[xmin - npoint-1, :])
        dcnoise_lower_ADC = np.average(DC_noise_ADC[xmin - npoint-1, :])
        print "DC noise at lower end of dynamic range: {} mV, {} ADC counts".format(dcnoise_lower,dcnoise_lower_ADC)
        effdrange = np.log2(drange/avdcnoise)
        effdrange_opt = np.log2(drange_ADC) - np.log2(dcnoiseADC_optimal)
        print "effective dynamic range (bits):" , effdrange, "(average)", effdrange_opt, "(optimal)"
        self.plot_avgTF(outdir,xmin=xmin,xmax=xmax)
        #print self.Vped
        return drange, INL, avdcnoise, effdrange, dcnoise_lower

# tf = TargetTF(infile)
# drange, INL, avdcnoise, eff_drange = tf.evaluate(outdir,npoint=10)
