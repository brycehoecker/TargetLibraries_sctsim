import sys
sys.path.append("/lustrehome/divenere/TargetC/new_software")
import TC_utils
import argparse
import os
import time
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import numpy as np
import cell_id_map
import scipy
from scipy.optimize import curve_fit, leastsq
import target_calib
from scipy import stats
from scipy import asarray as ar,exp
import yaml
from utils import *
from MyLogging import logger
import warnings
import enlighten
import pandas as pd
from itertools import groupby

output_results_mode="minmax"

def get_col_map(col_list):
    col_map=mpl.colors.get_named_colors_mapping() ## html codes for everycolor
    my_col=[]
    for i in range(len(col_list)):
        x = col_list[i]
        my_col.append(col_map[x])
    return my_col ###list of my colors' html codes

def get_colors(n_col):
    col=[]
    palette=['tab:blue','tab:orange','tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan','crimson','lightcoral','darkmagenta','royalblue','darkcyan','deepskyblue','sandybrown','lightseagreen','rosybrown','olive','mediumturquoise','dodgerblue','navajowhite','khaki','palegreen','indianred','lightsteelblue','forestgreen','lightgreen','lightblue','thistle','powderblue','salmon','bisque','lemonchiffon','peachpuff','mistyrose','wheat']
    for i in range(n_col):
        col.append(palette[i])

    return col

#def gaus_function1(x, logA, mu, sigma): ## gaussian function with log-normalization
#    A=10**logA
#    return A*np.exp(-(x-mu)**2/(2.*sigma**2))/sigma/(2*np.pi)**0.5

def exp_funct(x,p0,p1):
    return np.exp(p0+p1*x)

def lin_funct(x,p0,p1):
    return p0+p1*x

def gaus_function(x, A, mu,sigma): ## gaussian function
    return A*exp(-(x-mu)**2/(2*sigma**2))

def var_rel(y):
    """
    returns relative variation array
    var_rel_y has len(y)-1
    """
    len_y = len(y)
    var_rel_y = np.zeros(len(y),dtype=float)
    for i in range(1,len_y):
        var_rel_y[i] = (y[i]-y[i-1])/(y[i]+y[i-1])/2
    return var_rel_y[1:]

def OLD_read_cell_id(wf,chan,ped): ## read cell ids corresponding to samples in waveforms
    cell_ids_list=[]

    for ievt in range(wf.n_events):
        firstcell= wf.first_cell_ids[ievt] #[chan]
        block_id = int(firstcell / 32)
        phase_block = firstcell % 32
        cell_ids = ped.get_cell_ids(block_id,phase_block)
        cell_ids_list.append(cell_ids)

    cell_ids_list = np.array(cell_ids_list)
    block_id_map = np.array(ped.block_id_map)
    return cell_ids_list, block_id_map

def read_cell_id(wf): ## read cell ids corresponding to samples in waveforms
    ped = cell_id_map.pedestal(wf.n_samples)
    cell_ids_list=[]

    for ievt in range(wf.n_events):
        firstcell= wf.first_cell_ids[ievt]
        block_id = int(firstcell / 32)
        phase_block = firstcell % 32
        cell_ids = ped.get_cell_ids(block_id,phase_block)
        cell_ids_list.append(cell_ids)

    cell_ids_list = np.array(cell_ids_list)
    block_id_map = np.array(ped.block_id_map)
    return cell_ids_list, block_id_map

def plot_pedestal2d(pedestal,title="",ytitle="",xtitle="",outdir="",figname="figname"):
    pede = np.array(pedestal)
    plt.clf()
    plt.title(title)
    plt.ylabel(ytitle)
    plt.xlabel(xtitle)
    vmin = np.nanmin(pede)
    vmax = np.nanmax(pede)
    #vmin = np.nanmin(pede[pede>0])
    plt.imshow(pede,origin='lower',cmap='jet',vmin=vmin,vmax=vmax)
    plt.colorbar()
    plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
    plt.savefig(outdir+figname+".png")

    return 0


def plot_pedestal1d(ped_matrix,outdir="",figname=["figname"]*3, tag=""):
    #ped_matrix=ped_matrix_all[chan]
    #title="Mean pedestal vs cell - Channel %i%s" %(chan, tag)

    nblk = int((ped_matrix.shape[-1]-31)/32)
    ped = cell_id_map.pedestal(nblk*32)
    nblk_tot = ped.n_blocks
    tot_cells = nblk_tot*32
    blkmap = ped.block_id_map
    blkmap_new=[]
    for i in range(nblk_tot):
        blkmap_new.append(int(blkmap.index(i)))

    if nblk>8:
        ncol=2
    else:
        ncol=1


    xtitle="cell id"
    ytitle="ADC counts"
    plt.clf()
    ax = plt.subplot(111)
    is_first=False
    try:
        singleped_matrix=ped_matrix[:,32:64]
        singleped_matrix=np.reshape(singleped_matrix,int(tot_cells))
    except:
        is_first=True
        singleped_matrix=ped_matrix[:,0:32]
        singleped_matrix=np.reshape(singleped_matrix,int(tot_cells))

    plt.clf()
    plt.plot(singleped_matrix)
    if not is_first:
        plt.title("Pedestal - second slice - %s" %(tag))
    else:
        plt.title("Pedestal - first slice - %s" %(tag))

    plt.xlabel(xtitle)
    plt.ylabel(ytitle)
    plt.savefig(outdir+figname[0]+".png")
    plt.clf()

    #mask_all = np.ones(tot_cells).astype(bool)
    #a_all,b_all,r_all,p_all,e_all = stats.linregress(np.arange(tot_cells)[mask_all],singleped_matrix[mask_all])
    #delta_ped_all=singleped_matrix[mask_all] - (a_all*np.arange(tot_cells)[mask_all] + b_all)
    #err_all =  ( ( (delta_ped_all )**2 ).sum()/( mask_all.sum()-2) )**0.5
    #nspikes_all = len(np.where(np.logical_or(delta_ped_all < -5*err_all, delta_ped_all > 5*err_all))[0])
    #spikeregion = np.where(np.logical_or(delta_ped_all < -5*err_all, delta_ped_all > 5*err_all))[0]

    #print ("spikeregion size", len(spikeregion))
    #print ("spikeregion", spikeregion)
    #np.savetxt(outdir+figname[0]+"_spikeregion.txt", spikeregion)

    mask = np.zeros(tot_cells).astype(bool)
    mask[range(31, tot_cells, 32)]= True
    mask1 = np.logical_not(mask)
    a,b,r,p,e = stats.linregress(np.arange(tot_cells)[mask],singleped_matrix[mask])
    delta_ped=singleped_matrix[mask] - (a*np.arange(tot_cells)[mask] + b)
    err =  ( ( (delta_ped )**2 ).sum()/( mask.sum()-2) )**0.5
    nsigma = stats.norm.isf(1./mask.sum()/2.)
    spikeregion = np.where(np.logical_or(delta_ped < -nsigma*err, delta_ped > nsigma*err))[0]
    nspikes = len(spikeregion)

    a1,b1,r1,p1,e1 = stats.linregress(np.arange(tot_cells)[mask1],singleped_matrix[mask1])
    delta_ped1=singleped_matrix[mask1] - (a1*np.arange(tot_cells)[mask1] + b1)
    err1 =  ( ( (delta_ped1 )**2 ).sum()/( mask1.sum()-2) )**0.5
    nsigma1 = stats.norm.isf(1./mask1.sum()/2.)
    spikeregion1 = np.where(np.logical_or(delta_ped1 < -nsigma1*err, delta_ped1 > nsigma1*err1))[0]
    nspikes1 = len(spikeregion1)

    plt.plot(np.arange(tot_cells)[mask],singleped_matrix[mask],color='m',linestyle='--',linewidth=0.5,marker='o',markersize=0.5)
    plt.plot(np.arange(tot_cells)[mask1],singleped_matrix[mask1],color='b',linestyle='--',linewidth=0.5,marker='o',markersize=0.5)
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1,color='b')
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1+nsigma1*err1,color='b',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1-nsigma1*err1,color='b',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b,color='m')
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b+nsigma*err,color='m',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b-nsigma*err,color='m',linestyle='--',linewidth=0.7)
    if not is_first:
        plt.title("Pedestal - second slice - %s" %(tag))
    else:
        plt.title("Pedestal - first slice - %s" %(tag))
    plt.xlabel(xtitle)
    plt.ylabel(ytitle)
    plt.savefig(outdir+figname[0]+"_with_fit.png")
    mean0=np.mean(singleped_matrix[mask1])
    mean1=np.mean(singleped_matrix[mask])
    Nspikes = nspikes + nspikes1
    #logger.info("*****" + str(Nspikes))
    plt.clf()

    nb=3
    start=2
    avgped_matrix = 0
    avgped_matrix32 = 0
    hitped_matrix = 0
    hitped_matrix32 = 0
    for i in range(nblk+1):
        a = ped_matrix[np.roll(blkmap,i),32*i:31*(i+1)+i]
        #logical = np.logical_not(np.isnan(a))
        #aa = a[logical]
        b= (a>0).astype(int)
        avgped_matrix +=a
        hitped_matrix+=b
        if i<nblk:
            a = ped_matrix[np.roll(blkmap,i),31+32*i]
            avgped_matrix32 +=a
            b = (a>0).astype(int)
            hitped_matrix32 +=b
            plt.plot(np.reshape(ped_matrix[np.roll(blkmap,i),32*i:32*(i+1)],int(tot_cells))[start*32:(start + nb)*32],label=str(i))
    plt.legend(loc='best',ncol=ncol)
    plt.title("Pedestal vs Position after trigger - %s" %(tag))
    plt.ylabel(ytitle)
    plt.xlabel(xtitle)
    for ib in range(nb):
        numblock = blkmap[start + ib]
        text="block " + str(numblock)
        pos_x = (2*(ib) + 1)/2/nb
        pos_y = 0.99
        plt.text(pos_x, pos_y, text, fontsize=10,  horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    plt.savefig(outdir+figname[1]+".png")

    avgped_matrix /= hitped_matrix
    avgped_matrix[blkmap_new,:]
    avgped_matrix=np.reshape(avgped_matrix,int(tot_cells-nblk_tot))
    avgped_matrix32 /=hitped_matrix32
    avgped_matrix32[blkmap_new]
    avgped_matrix32=np.reshape(avgped_matrix32,int(nblk_tot))

    plt.clf()
    cap=np.delete(np.arange(tot_cells),np.arange(31,tot_cells,32))
    cap32=np.arange(31,tot_cells,32)
    plt.plot(cap,avgped_matrix,marker='o',markersize=0.7,linewidth=0.3,color='b')
    plt.plot(cap32,avgped_matrix32,marker='o',linestyle='--',markersize=0.7,linewidth=0.5,color='m')

    nspikes=0
    nspikes1=0
    a,b,r,p,e = stats.linregress(cap,avgped_matrix)
    delta_ped=avgped_matrix - (a*cap + b)
    err =  ( ( (delta_ped )**2 ).sum()/( len(cap)-2) )**0.5
    nsigma = stats.norm.isf(1./len(cap)/2.)
    spikeregion = np.logical_or(delta_ped < -nsigma*err, delta_ped > nsigma*err)
    spikeblocks = np.array([spikeregion[31*i:31*(i+1)].sum() for i in range(nblk_tot)])
    nspikes = len(np.where(spikeregion)[0])
    nspikeblocks = len(np.where(spikeblocks>15)[0]) ## blocks are considered bad if they have more than half cells with spikes
    a1,b1,r1,p1,e1 = stats.linregress(cap32,avgped_matrix32)
    delta_ped1=avgped_matrix32 - (a1*cap32 + b1)
    err1 =  ( ( (delta_ped1 )**2 ).sum()/( len(cap32)-2) )**0.5
    nsigma1 = stats.norm.isf(1./len(cap32)/2.)
    spikeregion1 = np.where(np.logical_or(delta_ped1 < -nsigma1*err1, delta_ped1 > nsigma1*err1))[0]
    nspikes1 = len(spikeregion1)
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b,color='b')
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b+nsigma*err,color='b',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a*np.arange(tot_cells)+b-nsigma*err,color='b',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1,color='m')
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1+nsigma1*err1,color='m',linestyle='--',linewidth=0.7)
    plt.plot(np.arange(tot_cells),a1*np.arange(tot_cells)+b1-nsigma1*err1,color='m',linestyle='--',linewidth=0.7)

    plt.title("Pedestal - average over slices - %s" %(tag))
    plt.xlabel(xtitle)
    plt.ylabel(ytitle)
    plt.savefig(outdir+figname[2]+".png")
    mean0=np.mean(avgped_matrix)
    mean1=np.mean(avgped_matrix32)
    rms0=np.sqrt(np.var(avgped_matrix))
    rms1=np.sqrt(np.var(avgped_matrix32))

    Nspikes = nspikes + nspikes1
    return mean0, mean1, rms0, rms1, Nspikes, b

def OLD_plot_wf(xaxis, wf, chan, totalcells=4096, title="", xtitle="", ytitle="", Nevt=300, figname="figname", outdir="", setrange=False):
    plt.clf()
    plt.xlabel(xtitle,fontsize=14)
    plt.ylabel(ytitle, fontsize=14)
    plt.title(title)
    plt.xlim(0,totalcells)
    if setrange:
        plt.ylim(0,4096)

    #for event in range (Nevt):
    #    print ("event", event, "channel", chan, "first cell --->",  wf.first_cell_ids[event][chan])
    plt.plot(xaxis.T, wf.waveforms[:Nevt,chan,:].T)

    plt.savefig(outdir + figname+".png")
    return 0

def plot_wf(xaxis, wfs, title="", xtitle="", ytitle="", figname="figname", outdir="", xlim=None, ylim=None):
    plt.clf()
    plt.xlabel(xtitle,fontsize=14)
    plt.ylabel(ytitle, fontsize=14)
    plt.title(title)
    if xlim is not None:
        plt.xlim(xlim[0],xlim[1])
    if ylim is not None:
        plt.ylim(ylim[0],ylim[1]) #4096

    #for event in range (Nevt):
    #    print ("event", event, "channel", chan, "first cell --->",  wf.first_cell_ids[event][chan])
    plt.plot(xaxis.T, wfs.T)

    plt.savefig(outdir + figname+".png")
    return 0

def plot_single_wf(xaxis, wf, chan, totalcells=4096,title="",xtitle="",ytitle="",figname="figname",outdir="",setrange=False):
    plt.clf()
    plt.xlabel(xtitle,fontsize=14)
    plt.ylabel(ytitle, fontsize=14)
    plt.title(title)
    plt.xlim(0,totalcells)
    if setrange:
        plt.ylim(0,4096)
    plt.plot(xaxis.T, wf.T)
    plt.savefig(outdir + figname+".png")
    return 0


def gauss_distribution(ax, data, bins=50, title="", xtitle="", ytitle="", dofit=False, figname="figname", outdir="", message="", limits=None, ylog=False, optimize_range=False, xlimits=None, range_tuple=None):
    """Gauss distribution"""
    ## limits must be a dictionary with keywords mean/sigma to check the mean and/or the sigma of the gaussian distribution. If only one keyword is present, that keyword only is checked. If both are present, then the keyword "both" is checked: if True a logical AND is performed to accept the "goodness" of the distribution, a logical OR otherwise. default is False.
    ## example: limits = {"mean":[-1,1], "sigma":[0,1], "both":True}
    #plt.clf()
    ax.cla()
    #ax = plt.subplot(111)
    ax.set_xlabel(xtitle)
    ax.set_ylabel(ytitle)
    ax.set_title(title)
    n,bins,patches = ax.hist(data, bins = bins, range=range_tuple, density = False, alpha = 0.75, facecolor='green')
    if ylog:
        ax.set_yscale("log")
    mean0=np.mean(data)
    var0=np.var(data)
    sigma0=np.sqrt(var0)

    try:
        if dofit:
            x = 0.5*(bins[1:]+bins[:-1])[:]
            y = n[:]
            yerr = y**0.5
            ### optimize range hist
            if optimize_range:
                yy = y[1:]+y[:-1]
                idx = np.where(yy>1)[0]
                binmin = idx[0]
                binmax = idx[-1]+1
            else:
                binmin=None
                binmax=None
            ## norm
            yn = np.max(y)
            y/=yn
            yerr/=yn
            x = np.array(x,dtype=np.float32)
            y = np.array(y, dtype=np.float32)
            yerr = np.array(yerr, dtype=np.float32)


            #maxtries = 10
            #tries = 0
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                coeff, var_matrix = curve_fit(gaus_function, x[binmin:binmax], y[binmin:binmax],sigma=yerr[binmin:binmax],absolute_sigma = True, p0=[1.,mean0,sigma0])
                for _w in w:
                    if _w.category is scipy.optimize.optimize.OptimizeWarning:
                        logger.debug("Reducing fit range in gaussian fit to +-5 rms.")
                        ## reduce range
                        xxmin = mean0-5*sigma0
                        xxmax = mean0+5*sigma0
                        logger.debug("New range: xxmin = {0} ... xxmax = {1}".format(xxmin, xxmax))

                        _mmask = (x>=xxmin)*(x<=xxmax)
                        xx = x[_mmask]
                        yy = y[_mmask]
                        yyerr = yerr[_mmask]
                        coeff, var_matrix = curve_fit(gaus_function, xx, yy,sigma=yyerr,absolute_sigma = True, p0=[1.,mean0,sigma0])
                        break
                        #tries = tries + 1
                        #if tries >= maxtries: break

            mean = coeff[1]
            sigma = np.abs(coeff[2])
            mean_err = var_matrix[1][1]**0.5
            sigma_err = var_matrix[2][2]**0.5
            limmax = np.max(data)#*5/3
            limmin=np.min(data)#*5/3
            xlims = (limmin,limmax)
            x_fit = np.linspace(xlims[0], xlims[1], 200)
            y_fit = gaus_function(x_fit,*coeff)

            ax.plot(x_fit,y_fit*yn,'r')
            mystr = 'mean = %.2f ADC counts\nsigma = %.2f ADC counts' % (mean, sigma)
            ax.text(0.99, 0.99, message, fontsize=10,  horizontalalignment='right', verticalalignment='top',transform = ax.transAxes)
            ax.text(0.01, 0.99, mystr, fontsize=10, horizontalalignment='left', verticalalignment='top', transform= ax.transAxes)
        else:
            mean=mean0
            sigma=sigma0
            mean_err = 0.
            sigma_err = 0.

    except:
        mean=mean0
        sigma=sigma0
        mean_err = 0.
        sigma_err = 0.



    ######## TODO MOVE ##########
    logger.debug("xlimits ------------------------------>" + str(xlimits))
    if xlimits is not None:
            #ax.text(xlimits[0], 0, 'min: {0} ADC units'.format(xlimits[0]), rotation=90, horizontalalignment='left', verticalalignment='bottom', color='r', alpha=0.7)
            #ax.text(xlimits[1], 0, 'max: {0} ADC units'.format(xlimits[1]), rotation=90, horizontalalignment='left', verticalalignment='bottom', color='r', alpha=0.7)

            ax.axvline(x=xlimits[0], color='r', linestyle='--', alpha=0.7)
            ax.axvline(x=xlimits[1], color='r', linestyle='--', alpha=0.7)



    if limits is not None and type(limits) is dict:
        outstr = ""
        ok_flag = sigma_flag = mean_flag = False
        lim_sigma = limits.get("sigma")
        lim_mean = limits.get("mean")
        if lim_sigma is not None:
            outstr += "$\sigma$: [{0:.1f} ... {1:.1f}], measured: {2:.1f}".format(lim_sigma[0], lim_sigma[1], sigma)
            if sigma >=lim_sigma[0] and sigma<=lim_sigma[1]:
                sigma_flag = True
            else:
                sigma_flag = False
#                if sigma <lim_sigma[0]:
#                    outstr += "$\sigma$ < {0:.1f}".format(lim_sigma[0])
#                else:
#                    outstr += "$\sigma$ > {0:.1f}".format(lim_sigma[1])
            outstr+="\n"
        if lim_mean is not None:
            if mean >=lim_mean[0] and sigma<=lim_mean[1]:
                outstr += "$\mu$: [{0:.2f} ... {1:.1f}], measured: {2:.1f}".format(lim_mean[0], lim_mean[1], mean)

                mean_flag = True
                #outstr += "{0:.2f} <= $\mu$ <= {1:.1f}".format(lim_mean[0], lim_mean[1])
            else:
                mean_flag = False
                #if mean < lim_mean[0]:
                #    outstr += "$\mu$ < {0:.1f}".format(lim_mean[0])
                #else:
                #    outstr += "$\mu$ > {0:.1f}".format(lim_mean[1])

        if lim_sigma is not None and lim_mean is not None:
            both_flag = limits.get("both")
            if both_flag:
                ok_flag = sigma_flag & mean_flag
            else:
                ok_flag = sigma_flag | mean_flag
        else:
            ok_flag = sigma_flag | mean_flag

        if ok_flag: #sigma >=limits[0] and sigma<=limits[1]:
            ax.text(0.85, 0.7, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
            ax.text(0.85, 0.6, outstr, fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
        else:
            ax.text(0.85, 0.7, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
            ax.text(0.85, 0.6, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)


    return mean,sigma, mean_err, sigma_err

def gauss_distribution2(data,bins=50,title="",xtitle="",ytitle="",dofit=False, figname="figname",outdir="",message="",ylog=False):
    plt.clf()
    ax = plt.subplot(111)
    plt.xlabel(xtitle,fontsize=14)
    plt.ylabel(ytitle,fontsize=14)
    plt.title(title)
    n,bins,patches = plt.hist(data, bins = bins, density = False, range = None, alpha = 0.75, facecolor='green')
    if ylog:
        plt.yscale("log")

    if dofit:
        x = 0.5*(bins[1:]+bins[:-1])[:]
        y = n[:]
        yn = np.max(y)
        y/=yn
        mean0 = sum(x*y)/len(x)
        sigma0=sum(y*(x - mean0)**2)/len(x)
        coeff, var_matrix = curve_fit(gaus_function, x, y,p0=[1,mean0,sigma0])
        logger.info( "mean0 --> " + str(mean0) + " sigma0 --> " + str(sigma0))
        logger.info ( "coeff-->" + str(coeff))
        mean = coeff[1]
        sigma = np.abs(coeff[2])
        y_fit = gaus_function(x,*coeff)
        plt.plot(x,y_fit*yn,'r')
        mystr = 'mean = %.2f ADC counts\nsigma = %.2f ADC counts' % (mean, sigma)
        plt.text(0.99, 0.99, message, fontsize=10,  horizontalalignment='right', verticalalignment='top',transform = ax.transAxes)
        plt.text(0.01, 0.99, mystr, fontsize=10, horizontalalignment='left', verticalalignment='top', transform=ax.transAxes)

    else:
        mean=np.mean(data)
        var=np.var(data)
        sigma=np.sqrt(var)

    plt.savefig(outdir+figname+".png")
    plt.clf()
    return mean,sigma

def spectral_distribution(data,nbins=150,title="",xtitle="",ytitle="",figname="figname",outdir="./"):
    plt.clf()
    plt.xlabel(xtitle,fontsize=14)
    plt.ylabel(ytitle,fontsize=14)
    plt.title(title)
    n,bins,patches = plt.hist(data, bins = nbins, density = False, range = None, alpha = 0.75, facecolor='green')
    plt.savefig(outdir+figname+".png")
    plt.clf()
    mean= np.mean(data)
    sigma = np.sqrt(np.var(data))

    return mean, sigma

def plots_canvas(figname,tag,outdir,minchannel,maxchannel):
    minasic= int(minchannel/16)
    maxasic=int(maxchannel/16)

    for asic in range(minasic,maxasic+1):
        command = "montage"
        if asic==4:
            continue
        for chan in range(16):
            if (chan + asic*16) in range(minchannel,maxchannel):
                command = command + " " + outdir + figname%(chan + asic*16,tag)+".png"
            else:
                command = command + " null:"
        command = command + " -mode Concatenate -geometry 300x240+2+2 -tile 4x4 " + outdir + figname[:2] + "_ASIC%i.png"%(asic)
        os.system(command)

    return 0

def plots_to_pdf(figname_list,tag,outdir,outname,minchannel,maxchannel,extrafigs=None):
    logger.log(logger.TEST_LEVEL_INFO, "Please wait while summary plots are being created...")
    outfile=outdir+outname
    pdf = MultipagePdf(outname=outfile)
    for figname in figname_list:
        for asic in range(4):
            fig_list = []
            for chan in range(16):
                ch = asic*16+chan
                if ch in range(minchannel,maxchannel):
                    fig_list.append(outdir+figname%(ch,tag)+".png")
            pdf.add_page_figures(fig_list)
    if extrafigs is not None:
        if type(extrafigs) is not list:
            pdf.add_page_figures([extrafigs])
        else:
            for fig in extrafigs:
                pdf.add_page_figures([fig])
    pdf.save_to_file()
    return 0


def eval_max_time_from_wf(wf,chan,t0,tag,outdir="",figname="figname"):
    fit_range = 5
    mean_t = []
    plt.clf()
    plt.xlabel("capacitor")
    plt.ylabel("ADC count")
    for i in range(len(wf.waveforms)):
        if i==100:
            plt.plot(range(wf.n_samples), wf.waveforms[i,chan,:])
        x = ar(range(t0-fit_range,t0+fit_range))
        y = ar(wf.waveforms[i,chan,t0-fit_range:t0+fit_range])
        yn = np.max(y)
        y/=yn
        mean0 = (sum(x*y)/sum(y)).astype(np.float32)
        sigma0 = np.abs(sum(y*(x - mean0)**2)/sum(y)).astype(np.float32)
        #coeff, var_matrix = curve_fit(gaus_function, x, y,p0=[1,mean0,sigma0])
        #y_fit = gaus_function(x,*coeff)
        #print(mean0,sigma0)
        y_fit = gaus_function(x,1,mean0,sigma0)
        if i==100:
            plt.plot(x,y_fit*yn,'r')
        #mean_t.append(coeff[1])

    plt.savefig(outdir+"7_WF_Gaus_one_evt_channel%i_event100.png"%(chan))
    plt.clf()
    title="Max time distribution from gaussian fit - channel %i%s" %(chan, tag)
    xtitle = "time (ns)"
    ytitle="Entries"
    #mean_t_wf, sigma_t_wf = gauss_distribution2(mean_t,bins=100,title=title,xtitle=xtitle,ytitle=ytitle,dofit=True, figname=figname,outdir=outdir,message="")
    ax=plt.gca()
    mean_t_wf, sigma_t_wf,_,_ = \
        gauss_distribution(
            ax=ax,
            data=mean_t,
            bins=100,
            title=title,
            xtitle=xtitle,
            ytitle=ytitle,
            dofit=True,
            message=""
        )


    plt.savefig(outdir+figname+".png")
    return mean_t_wf, sigma_t_wf




def eval_sigma_tau(wf,t0,outdir="",figname="figname",title=""):
    wf2=wf.copy()
    fit_range = 10
    mean_t = []
    plt.clf()
    plt.xlabel("time (ns)")
    plt.ylabel("ADC count")

    plt.plot(range(len(wf)), wf)
    plt.title(title)
    x = np.asarray(range(t0-fit_range,t0+fit_range))
    y = np.asarray(wf[t0-fit_range:t0+fit_range]).copy()
    yn = np.max(y)
    y/=yn
    mean0 = (sum(x*y)/sum(y)).astype(np.float32)
    sigma0 = np.abs(sum(y*(x - mean0)**2)/sum(y)).astype(np.float32)
    coeff, var_matrix = curve_fit(gaus_function, x, y,p0=[1,mean0,sigma0])
    #t0=int(np.round(coeff[1]))
    t0=int(coeff[1])
    x = np.asarray(range(t0-fit_range,t0+fit_range))
    y = np.asarray(wf[t0-fit_range:t0+fit_range]).copy()
    yn = np.max(y)
    y/=yn
    mean0 = (sum(x*y)/sum(y)).astype(np.float32)
    sigma0 = np.abs(sum(y*(x - mean0)**2)/sum(y)).astype(np.float32)
    coeff, var_matrix = curve_fit(gaus_function, x, y,p0=[1,mean0,sigma0])
    
    y_fit = gaus_function(x,*coeff)
    tmax = int(np.round(coeff[1]))
    
    
    mean_ampl_wf=wf[tmax]
            
    #print(mean0,sigma0)
    #y_fit = gaus_function(x,1,mean0,sigma0)
    plt.plot(x,y_fit*yn,'r')
    ymax=np.max(wf)
 
    t0=int(np.round(coeff[1]))
    dt=1
    x=ar(range(t0+dt,t0+100))
    y=ar(wf[t0+dt:t0+100])
    
    par, par_var = curve_fit(exp_funct, x, y,p0=[50,-0.5])
    par, par_var = curve_fit(exp_funct, x, y,p0=par)
    y_fit_exp=exp_funct(x,*par)
    par_err = np.sqrt(np.diag(par_var))
    plt.plot(x,y_fit_exp,'g')
    plt.savefig(outdir+figname+".png")

    return coeff[1],(np.sqrt(np.diag(var_matrix)))[1],mean_ampl_wf,np.abs(coeff[2]*2.35),2.35*(np.sqrt(np.diag(var_matrix)))[2],-1./par[1],par_err[1]/(par[1]**2)

    
def analyse_pedestal(fname_r0, fname_r1=None, fname_ped=None, outdir="./", ch0=0, nch=64, tag="", fast=True):
    logger.log(logger.TEST_LEVEL_INFO, "Starting pedestal analysis...")
    dpi=100
    Nevt_to_plot=100

    if tag!="" and not tag.startswith("_"):
        tag ="_"+tag

    minchannel=ch0
    maxchannel=ch0+nch
    if maxchannel>64:
        maxchannel = 64
    figname_list=['1_bufferscan_raw_channel%i%s', '2_bufferscan_pedsub_channel%i%s', '3_noise_distribution_channel%i%s', '4_Pedestal_map_channel%i%s', '4A_Pedestal_first_slice_channel%i%s', '4B_Pedestal_vs_Position_after_trigger_channel%i%s', '4C_Pedestal_avg_slices_channel%i%s','5_Hitmap_channel%i%s', '6_stddevmap_channel%i%s', '6A_Stddev_first_slice_channel%i%s', '6B_Stddev_vs_Position_after_trigger_channel%i%s', '6C_Stddev_avg_slices_channel%i%s','7_Mean_wf_channel%i%s']


    ### READING RAW DATA ###
    logger.log(logger.TEST_LEVEL_INFO, "Reading raw data {0}:".format(fname_r0))
    #logger.info("Reading file: " + fname_r0)
    wf_0 = TC_utils.Waveform(fname_r0)
    Nevents=wf_0.n_events
    Npixels=wf_0.n_pixels
    Nsamples=wf_0.n_samples

    ### READING PEDESTAL ###
    pedmap = TC_utils.Pedestal()
    if fname_ped is not None:
        pedmap.read_from_database(fname_ped)
    else:
        pedmap.calculate_from_waveforms(wf_0)
    totalcells = pedmap.n_max_block*32

    ### READING CAL DATA ###
    logger.log(logger.TEST_LEVEL_INFO, "Reading calibrated data {0}:".format(fname_r1))
    if fname_r1 is not None:
        logger.info("Reading file: " + fname_r1)
        wf_cal = TC_utils.Waveform(fname_r1)
    else:
        ## TO BE IMPLEMENTED: run-time r1 evaluation
        raise ValueError("No r1 file provided. Pedestal analysis is not possible")

    logger.info("Start analysis")
    all_sigma = []
    nspikes_tot = []
    os.system("mkdir -p " + outdir)
    ped_file = open(outdir+ "results_pedestal.txt","w")
    ped_file.write('ch\tped_av_0-30\tped_sigma_0-30\tped_av31\tped_sigma31\tsigma_noise\tOutliers\tPed0\n')

    fname = "limits.yaml"
    d={}
    with open(fname) as fptr:
            d = yaml.load(fptr, Loader=yaml.FullLoader)

    ped_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\n'.format(d['ch'][0], d['Ped_avg_0_30'][0], d['Ped_sigma_0_30'][0], d['Ped_avg_31'][0], d['Ped_sigma_31'][0], d['Sigma_noise'][0], d['Outliers'][0], d['Ped0'][0]))
    ped_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\n'.format(d['ch'][1], d['Ped_avg_0_30'][1], d['Ped_sigma_0_30'][1], d['Ped_avg_31'][1], d['Ped_sigma_31'][1], d['Sigma_noise'][1], d['Outliers'][1], d['Ped0'][1]))

    columns = ['ch', 'Ped_avg_0_30', 'Ped_sigma_0_30', 'Ped_avg_31', 'Ped_sigma_31', 'Sigma_noise', 'Outliers', 'Ped0']
    types = ['int32','float32','float32','float32','float32','float32','float32','float32']
    ped_output = MyOutput(columns=columns).set_types( types)




    #limits = ['99-99', '', '[99,99]', '9999', '9999', '9999', '99-99', '9999']
    #df_limits = pd.DataFrame(limits, columns=columns)
    #ped_output.append(df_limits)
    #ped_output.loc[len(ped_output), columns] = limits
    #ped_output.add_limits_to_output()
    #ped_output = ped_output.set_types( types)
    #print(ped_output)
    plt.figure()
    fig,ax = plt.subplots()
    fig.set_dpi(dpi)


    manager = enlighten.get_manager()
    #pbar = manager.counter(total=int(warmup_time*10.0), desc='DAQ warmup', unit='ticks')
    total = maxchannel-minchannel
    pbar = manager.counter(total=total, desc='Plotting channels', leave = False)

    for chan in range(minchannel,maxchannel):
        pbar.update()
        ped_output.loc[len(ped_output),"ch"]=chan
        plt.clf()
        #if chan%8==0:
        logger.info("Plotting channel " + str(chan))
        cell_ids_list, block_id_map=read_cell_id(wf_0)#,chan,ped)

        xtitle="capacitor"
        title="Events before pedestal correction - channel %i \n%i events, %i samples each%s" % (chan, Nevt_to_plot, Nsamples, tag)
        ytitle="raw ADC counts"
        figname = figname_list[0] % (chan, tag)
        plot_wf(cell_ids_list[:Nevt_to_plot], wf_0.waveforms[:Nevt_to_plot,chan,:],title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,xlim=[0,totalcells],ylim=[0,4096])

        title="Events after pedestal correction - channel %i \n%i events, %i samples each%s" % (chan, Nevt_to_plot, Nsamples, tag)
        ytitle="calibrated ADC counts"
        figname = figname_list[1] % (chan, tag)
        plot_wf(cell_ids_list[:Nevt_to_plot],wf_cal.waveforms[:Nevt_to_plot,chan,:],title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,xlim=[0,totalcells])


        title="Pedestal map - Channel %i%s" %(chan, tag)
        xtitle="sample"
        ytitle="block id"
        figname = figname_list[3] % (chan, tag)
        plot_pedestal2d(pedmap.pedmap[chan],title=title,ytitle=ytitle,xtitle=xtitle,outdir=outdir,figname=figname)

        figname=[figname_list[4]%(chan,tag),figname_list[5]%(chan,tag),figname_list[6]%(chan,tag)]
        mean0, mean1, rms0, rms1, nspikes, ped0 = plot_pedestal1d(pedmap.pedmap[chan], outdir=outdir,figname=figname, tag="Channel %i%s" %(chan, tag))
        nspikes_tot.append(nspikes)

        if not fast:
            logger.info("Doing extra plots in pedestal analysis...")
            title="Pedestal hitmap - Channel %i%s" %(chan,tag)
            figname=figname_list[7] % (chan, tag)
            plot_pedestal2d(pedmap.hitmap[chan],title=title,ytitle=ytitle,xtitle=xtitle,outdir=outdir,figname=figname)
            ## check hits in hitmap
            thr=1
            i_counts=0
            for j in range(len(pedmap.hitmap[chan])):
                for k in range(len(pedmap.hitmap[chan][j])):
                    if pedmap.hitmap[chan,j,k]<thr:
                        i_counts += 1
            if i_counts > 0:
                logger.warning("Less than " + str(thr) + " hits in " +str (i_counts) + "cells for channel " + str(chan) + " block " + str(j) + " cell " + str(k))


            title="Pedestal stddevmap - Channel %i%s" %(chan,tag)
            figname = figname_list[8] % (chan, tag)
            plot_pedestal2d(pedmap.stddevmap[chan],title=title,ytitle=ytitle,xtitle=xtitle,outdir=outdir,figname=figname)

            figname=[figname_list[9]%(chan,tag),figname_list[10]%(chan,tag),figname_list[11]%(chan,tag)]

            #figname=["6A_Stddev_first_slice_channel%i%s" %(chan, tag),"6B_Stddev_vs_Position_after_trigger_channel%i%s" % (chan, tag),"6C_Stddev_avg_slices_channel%i%s" % (chan, tag)]
            meanstddev0, meanstddev1, rmsstddev0, rmsstddev1, nspikes_stddev, std0 = plot_pedestal1d(pedmap.stddevmap[chan], outdir=outdir,figname=figname, tag="Channel %i%s" %(chan, tag))
            #ped_file.write(str(chan)+'\t'+ str(mean0) + '\t' + str(rms0) + '\t' + str(mean1) + '\t' +str(rms1) + '\t' + str(sigma_ch)+'\t'+ str(nspikes)+ '\t' + str(ped0) + '\n')

        title="Noise distribution - Channel %i%s" %(chan, tag)
        ytitle="Entries"
        xtitle="ADC counts"
        figname = figname_list[2] % (chan, tag)
        data=wf_cal.waveforms[:,chan,:].flatten()
        message= "Nsamples = "+str(Nsamples) + "\nNevents = "+str(Nevents) + "\ntotalEntries = " + str(len(data)) + "\nNoutliers = "+str(nspikes) #+ "\nUnderflow = " + str(uflow)+ "\nOverflow = " + str(oflow)
        logger.debug("Computing gauss distribution for channel {0}".format(chan))

        ax=plt.gca()
        ############## removing entries above 3500  <----------- TO BE CHECKED IN TARGET CALIB
        data = data[data<3500]
        mean_ch,sigma_ch,_tmp1,_tmp2 = \
            gauss_distribution(
                ax=ax,
                data=data,
                bins=65,
                title=title,
                xtitle=xtitle,
                ytitle=ytitle,
                dofit=True,
                message=message,
                limits={"sigma":ped_output.limits["Sigma_noise"]},
                ylog=False,
                optimize_range=True
            )
        plt.savefig(outdir+figname+".png")
        all_sigma.append(sigma_ch)


        ped_file.write("{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\n".format(chan,mean0,rms0,mean1,rms1,sigma_ch,nspikes,ped0))
        ped_output.loc[ped_output.ch==chan, columns] = [chan,mean0,rms0,mean1,rms1,sigma_ch,nspikes,ped0]
        ## check on last row
        flag1 = ped_output.check_quality("Sigma_noise", rows=len(ped_output)-1)
        flag2 = ped_output.check_quality("Outliers", rows=len(ped_output)-1)
        flag = flag1 & flag2
        logger.debug("Flag for sigma_noise on channel "+str(chan)+" is: " +str(flag)) #### debug output

        title="Mean wf - channel %i%s" %(chan,tag)
        xtitle="sample"
        ytitle="Mean wf (ADC counts)"
        mean_wf = np.mean(wf_cal.waveforms[:,chan,:],axis=0)
        figname= figname_list[12]%(chan,tag)
        plot_single_wf(np.arange(Nsamples), mean_wf, chan, totalcells=Nsamples,title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,setrange=False)

    pbar.close()
    manager.stop()


    ch_id=np.arange(minchannel,maxchannel)

    extrafigs=[]
    plt.clf()
    ax=plt.gca()
    plot_noise_summary(ax, ch_id, all_sigma)
    plt.savefig(outdir+ "8_noise_summary.png")#, dpi=dpi)
    extrafigs.append(outdir+ "8_noise_summary.png")

    ped_file.close()
    ped_output.save_to_file(outdir+ "results_pedestal2.txt", sep=";")
    ped_output = MyOutput(data=pd.read_csv(outdir+ "results_pedestal2.txt", header=0, sep=";"))
    ped_output.add_limits_to_output(mode=output_results_mode)

    flag1 = ped_output.check_quality("Sigma_noise")
    #                                     rows=list(np.arange(1,len(ped_output)))) #first row after header is limits row: do not check!!!
    flag2 = ped_output.check_quality("Outliers")
    #                                     rows=list(np.arange(1,len(ped_output)))) #first row after header is limits row: do not check!!!
    nbad_ch = np.logical_not(flag1*flag2).sum()

    ped_output.save_to_html(outdir+ "results_pedestal.html")
    ped_output.save_to_file(outdir+ "results_pedestal.txt", sep="\t", align_colnames=True)

    # Sigma Plot
    flag_sigma = all(flag1)
    ax = plt.gca()
    plot_sigma_summary(
        ax=ax,
        ch_id=ch_id,
        all_sigma=all_sigma,
        print_text=True,
        ok_flag=flag_sigma
    )
    extrafigs.append(outdir + "9_summary_sigma.png")
    plt.savefig(outdir + "9_summary_sigma.png")

    # Outliers Plot
    outliers_flag = all(flag2)
    ax = plt.gca()
    plot_outliers_summary(
        ax=ax,
        ch_id=ch_id,
        nspikes_tot=nspikes_tot,
        totalcells=totalcells,
        print_text=True,
        ok_flag=outliers_flag
    )
    extrafigs.append(outdir + "10_outliers.png")
    plt.savefig(outdir + "10_outliers.png")




    #for figname in figname_list:
    #    plots_canvas(figname,tag,outdir,minchannel,maxchannel)
    #plots_to_pdf(figname_list,tag,outdir,"results_pedestal_plots.pdf",minchannel,maxchannel, extrafigs=extrafigs)
    logger.log(logger.TEST_LEVEL_INFO, "Finished pedestal analysis.")
    #fig = plt.figure(figsize=(20,20))
    ################### gs = fig.add_gridspec(2,2)


    fig = plt.figure(figsize=(4*2,3*2))

    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(212)
    plot_noise_summary(ax1, ch_id, all_sigma)
    plot_sigma_summary(
        ax=ax2,
        ch_id=ch_id,
        all_sigma=all_sigma,
        print_text=True,
        ok_flag=flag_sigma
    )
    plot_outliers_summary(
        ax=ax3,
        ch_id=ch_id,
        nspikes_tot=nspikes_tot,
        totalcells=totalcells,
        print_text=True,
        ok_flag=outliers_flag
    )

    plt.tight_layout()
    plt.savefig(outdir+"11_results_pedestal_plots.png")



    """
    if flag2==1:
        print(flag2)
        ax3.text(0.7, 1, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
        #ax3.text(0.7, 0.2, "Outliers limits: [{0:.0f},{1:.0f}]".format(ped_output.limits["Outliers"][0],ped_output.limits["Outliers"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    else:
        ax3.text(0.7, 0.3, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
        ax3.text(0.7, 0.2, "Outliers limits: [{0:.0f},{1:.0f}]".format(ped_output.limits["Outliers"][0],ped_output.limits["Outliers"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
        #outstr = "bad channels: "+" ".join(bad_ch)
        ax3.text(0.7, 0.1, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    """

    logger.log(logger.TEST_LEVEL_INFO, "Finished pedestal analysis.")
    del wf_0, wf_cal
    return nbad_ch

def analyse_signal(fname_r1, fname_r0=None, outdir="./", ch0=0, nch=64, tag="",pulse_analysis=False,dac_analysis=False):
    logger.log(logger.TEST_LEVEL_INFO, "Starting signal analysis.")
    logger.info("Signal analysis...")
    dpi=100
    Nevt_to_plot=100

    if tag!="" and not tag.startswith("_"):
        tag ="_"+tag

    minchannel=ch0
    maxchannel=ch0+nch

    if maxchannel>64:
        maxchannel = 64
    do_ct = False
    if do_ct:
        signal_ch_list = [32]
        ct_file = open(outdir + "results_ct.txt","w")
        ct_file.write('Signal_channel\tCT_channels[16]\n')
        mean_amplitude = []
    do_timediff = False
    if do_timediff:
        timediff_file = open(outdir + "results_timediff_ch0_"+str(ch0)+".yaml","w")

    res_filename = outdir+ "results_signal.txt"
    res_file = open(res_filename,"w")
    #res_file.write('Channel\tMax_ampl\tSigma_max_ampl\ttmax\tSigma_tmax\ttmax_wf\tSigma_tmax_wf\tMean_ampl_fixed_t\tSigma_ampl_fixed_t\n')
    if pulse_analysis:
        res_file.write('ch\tmax_ampl\tsigma_max_ampl\ttmaximum\tsigma_tmax\ttmaximum_wf\tsigma_tmax_wf\tmean_ampl_sipm\terr_ampl_sipm\tfwhm_mean_ampl_sipm\terr_fwhm\tpulse_tau\tpulse_tau_sigma\n')
    elif dac_analysis:
        res_file.write('ch\tmax_ampl\tsigma_max_ampl\ttmaximum\tsigma_tmax\ttmaximum_wf\tsigma_tmax_wf\tampl_fix_t\tsigma_ampl_fix_t\tmax_ampl_mean_wf\tmax_ampl_mean_wf_err\n')
    else:
        res_file.write('ch\tmax_ampl\tsigma_max_ampl\ttmaximum\tsigma_tmax\ttmaximum_wf\tsigma_tmax_wf\tampl_fix_t\tsigma_ampl_fix_t\n')
    fname = "limits.yaml"
    d={}
    with open(fname) as fptr:
            d = yaml.load(fptr, Loader=yaml.FullLoader)

    if pulse_analysis:
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\t{9:.3e}\t{10:.3e}\n'.format(d['ch'][0], d['max_ampl'][0], d['sigma_max_ampl'][0], d['tmaximum'][0], d['sigma_tmax'][0], d['tmaximum_wf'][0], d['sigma_tmax_wf'][0], d['mean_ampl_sipm'][0], d['mean_ampl_sipm_sigma'][0],d['fwhm_mean_ampl_sipm'][0],d['fwhm_mean_ampl_sipm_sigma'][0],d['pulse_tau'][0],d['pulse_tau_sigma'][0]))
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\t{9:.3e}\t{10:.3e}\n'.format(d['ch'][1], d['max_ampl'][1], d['sigma_max_ampl'][1], d['tmaximum'][1], d['sigma_tmax'][1], d['tmaximum_wf'][1], d['sigma_tmax_wf'][1], d['mean_ampl_sipm'][1], d['mean_ampl_sipm_sigma'][1],d['fwhm_mean_ampl_sipm'][1],d['fwhm_mean_ampl_sipm_sigma'][1],d['pulse_tau'][1],d['pulse_tau_sigma'][1]))
        
        #res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\t{9:.3e}\t{10:.3e}\n'.format(d['ch'][0], d['max_ampl'][0], d['sigma_max_ampl'][0], d['tmaximum'][0], d['sigma_tmax'][0], d['tmaximum_wf'][0], d['sigma_tmax_wf'][0], d['ampl_fix_t'][0], d['sigma_ampl_fix_t'][0],d['pulse_tau'][0],d['pulse_tau_sigma'][0] ))
        #res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n'.format(d['ch'][1], d['max_ampl'][1], d['sigma_max_ampl'][1], d['tmaximum'][1], d['sigma_tmax'][1], d['tmaximum_wf'][1], d['sigma_tmax_wf'][1], d['ampl_fix_t'][1], d['sigma_ampl_fix_t'][1],d['pulse_tau'][1],d['pulse_tau_sigma'][1]))
    elif dac_analysis:
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n'.format(d['ch'][0], d['max_ampl'][0], d['sigma_max_ampl'][0], d['tmaximum'][0], d['sigma_tmax'][0], d['tmaximum_wf'][0], d['sigma_tmax_wf'][0], d['ampl_fix_t'][0], d['sigma_ampl_fix_t'][0],d['max_ampl_mean_wf'][0],d['max_ampl_mean_wf_err'][0]))
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n'.format(d['ch'][1], d['max_ampl'][1], d['sigma_max_ampl'][1], d['tmaximum'][1], d['sigma_tmax'][1], d['tmaximum_wf'][1], d['sigma_tmax_wf'][1], d['ampl_fix_t'][1], d['sigma_ampl_fix_t'][1],d['max_ampl_mean_wf'][1],d['max_ampl_mean_wf_err'][1]))
    else:
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n'.format(d['ch'][0], d['max_ampl'][0], d['sigma_max_ampl'][0], d['tmaximum'][0], d['sigma_tmax'][0], d['tmaximum_wf'][0], d['sigma_tmax_wf'][0], d['ampl_fix_t'][0], d['sigma_ampl_fix_t'][0]))
        res_file.write('{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n'.format(d['ch'][1], d['max_ampl'][1], d['sigma_max_ampl'][1], d['tmaximum'][1], d['sigma_tmax'][1], d['tmaximum_wf'][1], d['sigma_tmax_wf'][1], d['ampl_fix_t'][1], d['sigma_ampl_fix_t'][1]))


    #columns = ['Channel', 'Max_ampl','Sigma_max_ampl','Time_of_max','Sigma_time_of_max','Time_of_max_wf','Sigma_time_of_max_wf','Mean_ampl_fixed_t','Sigma_ampl_fixed_t']
    if pulse_analysis:
        #columns = ['ch', 'max_ampl','sigma_max_ampl','tmaximum','sigma_tmax','tmaximum_wf','sigma_tmax_wf','mean_ampl_sipm','fwhm_mean_ampl_sipm','pulse_tau','pulse_tau_sigma']
        columns = ['ch', 'max_ampl','sigma_max_ampl','tmaximum','sigma_tmax','tmaximum_wf','sigma_tmax_wf','mean_ampl_sipm','mean_ampl_sipm_sigma','fwhm_mean_ampl_sipm','fwhm_mean_ampl_sipm_sigma','pulse_tau','pulse_tau_sigma']
        types = ['int32','float32','float32','float32','float32','float32','float32','float32', 'float32','float32','float32','float32','float32','float32']
    elif dac_analysis:
        columns = ['ch', 'max_ampl','sigma_max_ampl','tmaximum','sigma_tmax','tmaximum_wf','sigma_tmax_wf','ampl_fix_t','sigma_ampl_fix_t','max_ampl_mean_wf','max_ampl_mean_wf_err']
        types = ['int32','float32','float32','float32','float32','float32','float32','float32', 'float32','float32','float32']
    else:
        columns = ['ch', 'max_ampl','sigma_max_ampl','tmaximum','sigma_tmax','tmaximum_wf','sigma_tmax_wf','ampl_fix_t','sigma_ampl_fix_t']
        types = ['int32','float32','float32','float32','float32','float32','float32','float32', 'float32']
    sig_output = MyOutput(columns=columns).set_types( types)

    mean_max_ampl_vals = []
    sigma_max_ampl_vals = []
    jitter_val = []
    mean_t_vals = []
    # only used in pulse_analysis
    meanwf_ampl_vals=[]
    meanwf_ampl_err=[]
    meanwf_fwhm_vals=[]
    meanwf_tau_vals=[]
    err_ampl_vals=[]
    err_fwhm_vals=[]
    err_tau_vals=[]
        
    ### READING RAW DATA ###
    if fname_r0 is not None:
        logger.info("Reading raw file: " + fname_r0)
        wf_0 = TC_utils.Waveform(fname_r0)

    ### READING CAL DATA ###
    logger.info ("Reading file: " + fname_r1)
    wf_cal = TC_utils.Waveform(fname_r1)
    logger.info("After waveform")
    #wf_cal.filter_events(fci_min=15000)
    #wf_cal.filter_events_by_stale()


    Nevents=wf_cal.n_events
    Npixels=wf_cal.n_pixels
    Nsamples=wf_cal.n_samples
    ped = cell_id_map.pedestal(Nsamples)
    cell_ids_list, block_id_map=read_cell_id(wf_cal)#,0,ped)
    mask = np.ones(Nevents).astype(bool)
    #fcimin = 511*32
    fcimin = 510*32 # --> this part discards the events that have a cell inside the last block (511) or the block before the last one (510)
    #probably there is no need to discard the block before the last one...
    fcimax = 512*32
    for evt in range(Nevents):
        cell_ids = cell_ids_list[evt]
        if ((cell_ids>=fcimin)*(cell_ids<fcimax)).any():
            mask[evt]=False

    if Nevents > 0:
      mask[0]=False #temporary solution, the first event for some reason does not correspond to a pulse?

    wf_cal.waveforms = wf_cal.waveforms[mask]
    #wf_cal.n_events = len(wf_cal.waveforms)
    Nevents = wf_cal.n_events

    #figname_list=['1_Raw_events_channel%i%s', '2_Calibrated_events_channel%i%s', '3_max_distribution_channel%i%s', '4_Time_of_max_amplitude_channel%i%s','5_Amplitude_distribution_at_fixed_t_channel%i%s','6_Mean_wf_channel%i%s','8_Max_time_wf_gauss_fit_channel%i%s']
    #Andrea: temporary removed figure 8 that doesn't work
    if pulse_analysis:
        figname_list=['1_Raw_events_channel%i%s', '2_Calibrated_events_channel%i%s', '3_max_distribution_channel%i%s', '4_Time_of_max_amplitude_channel%i%s','5_Amplitude_distribution_at_fixed_t_channel%i%s','6_Mean_wf_fit_channel%i%s']
    else:
        figname_list=['1_Raw_events_channel%i%s', '2_Calibrated_events_channel%i%s', '3_max_distribution_channel%i%s', '4_Time_of_max_amplitude_channel%i%s','5_Amplitude_distribution_at_fixed_t_channel%i%s','6_Mean_wf_channel%i%s']

    plt.figure()
    fig,ax = plt.subplots()

    manager = enlighten.get_manager()
    total = maxchannel-minchannel
    pbar = manager.counter(total=total, desc='Plotting channels', leave = False)

    for chan in range(minchannel,maxchannel):
        pbar.update()
        sig_output.loc[len(sig_output),"ch"]=chan
        #if chan%8==0:
        #    logger.log(logger.TEST_LEVEL_INFO, "Plotting channel " + str(chan))
        plt.clf()
        fig.set_dpi(dpi)
        #if chan%8==0:
        #    logger.info("Plotting channel " + str(chan))
        if fname_r0 is not None:
            title="All raw events - channel %i \n%i events, %i samples each%s" % (chan, Nevt_to_plot, Nsamples, tag)
            ytitle="ADC counts"
            xtitle="sample"
            figname = figname_list[0] % (chan, tag)
            plot_wf(np.arange(Nsamples),wf_0.waveforms[:Nevt_to_plot,chan,:],title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,xlim=[0,Nsamples],ylim=[0,4096])

        title="Events after pedestal subtraction - channel %i \n%i events, %i samples each%s" % (chan, Nevt_to_plot, Nsamples, tag)
        ytitle="calibrated ADC counts"
        xtitle="sample"
        figname = figname_list[1] % (chan, tag)
        plot_wf(np.arange(Nsamples),wf_cal.waveforms[:Nevt_to_plot,chan,:],title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,xlim=[0,Nsamples])

        wf_cal.subtract_baseline(t_bsl=20)
        ytitle="Entries"
        xtitle="ADC counts"
        title="Max distribution - Channel %i%s" %(chan, tag)
        figname= figname_list[2] % (chan, tag)
        data=np.max(wf_cal.waveforms[:,chan,:], axis=1)
        #data = data[data>0]
        ax=plt.gca()
        mean_max,sigma_max, mean_max_err, sigma_max_err = \
            gauss_distribution(
                ax=ax,
                data=data[data>0],
                bins=50,
                title=title,
                xtitle=xtitle,
                ytitle=ytitle,
                dofit=True,
                figname=figname,
                outdir=outdir,
                ylog=False,
                optimize_range=True
            )
        plt.savefig(outdir+ figname + ".png")
        mean_max_ampl_vals.append(mean_max)
        sigma_max_ampl_vals.append(sigma_max)

        a = wf_cal.waveforms[:,chan,:].tolist()
        time_of_max = []
        for i in range(len(data)):
            if data[i]>0:
                time_of_max.append(a[i].index(data[i]))
        title = "Time of max amplitude - channel %i%s"%(chan,tag)
        xtitle="Time (ns)"
        figname= figname_list[3] %(chan,tag)
        ax = plt.gca()
        mean_t, sigma_t, mean_t_err, sigma_t_err = \
            gauss_distribution(
                ax=ax,
                data=time_of_max,
                bins=127,
                title=title,
                xtitle=xtitle,
                ytitle=ytitle,
                dofit=False,
                ylog=False
            )
        plt.savefig(outdir+ figname + ".png")
        mean_t_vals.append(mean_t)
        jitter_val.append(sigma_t)
        t0=int(mean_t+0.5)

        #t0=mean_t
        title="Amplitude distribution at t %i ns - channel %i%s" %(t0,chan, tag)
        figname= figname_list[4] % (chan, tag)
        data=wf_cal.waveforms[:,chan,t0]
        data = data[data>0]
        xtitle="Amplitude (ADC counts)"
        ytitle="Entries"
        nbins=50
        mean_amp_fixed_t, sigma_mean_amp_fixed_t = spectral_distribution(data,nbins,title,xtitle,ytitle,figname,outdir)
        ##andrea:disabled this temporarily###mean_amp_fixed_t, sigma_mean_amp_fixed_t,mean_amp_fixed_t_err,  sigma_mean_amp_fixed_t_err = gauss_distribution(data,nbins,title,xtitle,ytitle,True,figname,outdir, log=False)


        mean_wf = np.mean(wf_cal.waveforms[:,chan,:],axis=0)
        mean_wf_err=np.sqrt(np.var(wf_cal.waveforms[:,chan,:],axis=0))
        if not pulse_analysis:
            title="Mean wf - channel %i%s" %(chan,tag)
            xtitle="capacitor"
            ytitle="Mean wf (ADC counts)"
            figname= figname_list[5]%(chan,tag)
            plot_single_wf(np.arange(Nsamples), mean_wf, chan, totalcells=Nsamples,title=title,xtitle=xtitle,ytitle=ytitle,figname=figname,outdir=outdir,setrange=False)
            if do_ct:
                mean_amplitude.append(np.max(mean_wf))

            #if chan==132 and pulse_analysis:
            #    figname = figname_list[7]%(chan,tag)
            #    mean_t_wf, sigma_t_wf = eval_max_time_from_wf(wf_cal,chan,t0,tag,outdir,figname)
            #else:
            #    mean_t_wf = 0
            #    sigma_t_wf = 0
        
        if pulse_analysis:
            title="Mean wf with fit - channel %i%s" %(chan,tag)
            figname = figname_list[5]%(chan,tag)
            mean_t_wf,sigma_mean_t_wf,mean_ampl_gaus, fwhm_t_wf,err_fwhm,pulse_tau,pulse_tau_sigma = eval_sigma_tau(mean_wf,t0,outdir,figname,title)
        else:
            mean_t_wf = 0
            sigma_mean_t_wf = 0
            mean_ampl_gaus = 0
            fwhm_t_wf = 0
            err_fwhm=0
            pulse_tau=0
            pulse_tau_sigma=0
            
        mean_wf_max=np.max(mean_wf)
        mean_wf_max_err=mean_wf_err[np.argmax(mean_wf)]

        meanwf_ampl_vals.append(mean_wf_max)
        meanwf_ampl_err.append(mean_wf_max_err)
        meanwf_fwhm_vals.append(fwhm_t_wf)
        meanwf_tau_vals.append(pulse_tau)
        err_ampl_vals.append(sigma_mean_t_wf)
        err_fwhm_vals.append(err_fwhm)
        err_tau_vals.append(pulse_tau_sigma)
        
        #res_file.write(str(chan) + '\t' + str(mean_max) + '\t' +str(sigma_max) + '\t'+ str(mean_t) + '\t' + str(sigma_t) +'\t' + str(mean_t_wf) + '\t' + str(sigma_t_wf) + '\t' +str(mean_amp_fixed_t) + '\t' + str(sigma_mean_amp_fixed_t) + '\n')
        if pulse_analysis:
            #res_file.write("{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\t{9:.3e}\t{10:.3e}\t{11:.3e}\n"format(chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, sigma_t_wf, mean_ampl_gaus,mean_amp_fixed_t, sigma_mean_amp_fixed_t,tau,sigma_tau))
            res_file.write("{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\t{9:.3e}\n".format(chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf,sigma_mean_t_wf,mean_wf_max,mean_wf_max_err, fwhm_t_wf,err_fwhm,pulse_tau,pulse_tau_sigma))
            #sig_output.loc[sig_output.ch==chan, columns] = [chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, sigma_t_wf,mean_ampl_gaus, mean_amp_fixed_t, sigma_mean_amp_fixed_t,tau,sigma_tau]
            sig_output.loc[sig_output.ch==chan, columns] = [chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf,sigma_mean_t_wf,mean_wf_max,mean_wf_max_err,fwhm_t_wf,err_fwhm,pulse_tau,pulse_tau_sigma]
        elif dac_analysis:
            res_file.write("{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n".format(chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, fwhm_t_wf, mean_amp_fixed_t, sigma_mean_amp_fixed_t,mean_wf_max,mean_wf_max_err))
            sig_output.loc[sig_output.ch==chan, columns] = [chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, fwhm_t_wf, mean_amp_fixed_t, sigma_mean_amp_fixed_t,mean_wf_max,mean_wf_max_err]
        else:
            res_file.write("{0}\t{1:.3e}\t{2:.3e}\t{3:.3e}\t{4:.3e}\t{5:.3e}\t{6:.3e}\t{7:.3e}\t{8:.3e}\n".format(chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, fwhm_t_wf, mean_amp_fixed_t, sigma_mean_amp_fixed_t))
            sig_output.loc[sig_output.ch==chan, columns] = [chan,mean_max,sigma_max,mean_t,sigma_t, mean_t_wf, fwhm_t_wf, mean_amp_fixed_t, sigma_mean_amp_fixed_t]

    pbar.close()
    manager.stop()
    
    res_file.close()
    df=pd.DataFrame(sig_output)
    res_dict=df.to_dict('index')
    with open(outdir+"results_dict.yaml","w") as fptr:
        yaml.dump(res_dict,fptr)
        
    sig_output.save_to_file(outdir+ "results_signal2.txt", sep=";")
    sig_output = MyOutput(data=pd.read_csv(outdir+ "results_signal2.txt",
                                           header=0, sep=";"))
    sig_output.add_limits_to_output(mode=output_results_mode)

    
    if pulse_analysis:
        # Check quality on sig_output for "mean_ampl_sipm"
        flag1 = sig_output.check_quality("mean_ampl_sipm")
        # Check quality on sig_output for "fwhm_mean_ampl_sipm"
        flag2 = sig_output.check_quality("fwhm_mean_ampl_sipm")
        # Check quality on sig_output for "pulse_tau"
        flag3 = sig_output.check_quality("pulse_tau")
    elif dac_analysis:
        # Check quality on sig_output for "max_ampl"
        flag1 = sig_output.check_quality("max_ampl")
        # Check quality on sig_output for "sigma_max_ampl"
        flag2 = sig_output.check_quality("sigma_max_ampl")
        # Check quality on sig_output for "max_ampl_mean_wf"
        flag3 = sig_output.check_quality("max_ampl_mean_wf")
    else:     
        # Check quality on sig_output for "max_ampl"
        flag1 = sig_output.check_quality("max_ampl")
        # Check quality on sig_output for "sigma_max_ampl"
        flag2 = sig_output.check_quality("sigma_max_ampl")
        # Get number of bad channels
    nbad_ch = np.logical_not(flag1*flag2).sum()
    
    sig_output.save_to_html(outdir+ "results_signal.html")
    sig_output.save_to_file(outdir+ "results_signal.txt", sep="\t", align_colnames=True)

    extrafigs=[]

    title = "Jitter"
    xtitle = "Jitter (ns)"
    ytitle = "Entries"
    figname = "7_Jitter_distribution"
    #jitter,sigma_jitter=gauss_distribution2(jitter_val,20,title,xtitle,ytitle,False,figname,outdir)
    ax=plt.gca()
    jitter,sigma_jitter,_,_= \
        gauss_distribution(
            ax=ax,
            data=jitter_val,
            bins=20,
            title=title,
            xtitle=xtitle,
            ytitle=ytitle,
            dofit=False,
            figname=figname,
            outdir=outdir
        )
    plt.savefig(outdir+figname+".png")

    extrafigs.append(outdir+figname+".png")

    plt.clf()
    ch_id=np.arange(minchannel,maxchannel)
    plt.title("Jitter", fontsize=16)
    plt.xlabel("Channel id")
    #ax.set_xlim(0,64)
    plt.ylabel(xtitle)
    plt.errorbar(ch_id,jitter_val, marker='o',markersize=4,linestyle=None)
    plt.savefig(outdir+ "8_Jitter_scatter.png")#, dpi=dpi)
    extrafigs.append(outdir+ "8_Jitter_scatter.png")


    ch_id=np.arange(minchannel,maxchannel)
    plt.clf()


    if not pulse_analysis:
        ax=plt.gca()
        max_ampl_flag = all(flag1)
        plot_max_ampl_distribution(ax, ch_id, mean_max_ampl_vals, print_text=True,ok_flag=max_ampl_flag)
        #plt.title("max_ampl(mean) distribution", fontsize=16)
        #plt.xlabel("max_ampl(mean)")
        #ax.set_xlim(0,64)
        #plt.ylabel("Entries")
        #n_max_ampl,bins_max_ampl,patches_max_ampl = plt.hist(mean_max_ampl_vals, bins = 20, density = False, range = None, alpha = 0.75, facecolor='green')
        plt.savefig(outdir+ "9_mean_max_ampl_distribution.png")#, dpi=dpi)
        extrafigs.append(outdir+ "9_mean_max_ampl_distribution.png")

        plt.clf()
        ax = plt.gca()
        plot_max_ampl_summary(ax, ch_id, mean_max_ampl_vals, print_text=True,ok_flag=max_ampl_flag)
        #ch_id=np.arange(minchannel,maxchannel)
        #plt.title("max_ampl", fontsize=16)
        #plt.xlabel("Channel id")
        #ax.set_xlim(0,64)
        #plt.ylabel("max_ampl(mean)")
        #plt.errorbar(ch_id,mean_max_ampl_vals, marker='o',markersize=4,linestyle=None)
        plt.savefig(outdir+ "10_mean_max_ampl_scatter.png")#, dpi=dpi)
        extrafigs.append(outdir+ "10_mean_max_ampl_scatter.png")

        plt.clf()
        ax = plt.gca()
        s_max_ampl_flag = all(flag2)
        plot_sigma_max_ampl_distribution(ax, ch_id, sigma_max_ampl_vals,print_text=True, ok_flag=s_max_ampl_flag)
        #plt.title("sigma_max_ampl distribution", fontsize=16)
        #plt.xlabel("sigma_max_ampl")
        #ax.set_xlim(0,64)
        #plt.ylabel("Entries")
        #n_sigma_max_ampl,bins_sigma_max_ampl,patches_sigma_max_ampl = plt.hist(
        #    sigma_max_ampl_vals, bins = 20, density = False, range = None,
        #    alpha = 0.75, facecolor='green')
        plt.savefig(outdir+ "11_sigma_max_ampl_distribution.png")#, dpi=dpi)
        extrafigs.append(outdir+ "11_sigma_max_ampl_distribution.png")

        plt.clf()
        ax = plt.gca()
        plot_sigma_max_ampl_summary(ax, ch_id, sigma_max_ampl_vals,print_text=True, ok_flag=s_max_ampl_flag)
        plt.savefig(outdir+ "12_sigma_max_ampl_scatter.png")#, dpi=dpi)
        extrafigs.append(outdir+ "12_sigma_max_ampl_scatter.png")
        
        fig = plt.figure(figsize=(5*2,5*2))

        ax1 = plt.subplot(221)
        ax2 = plt.subplot(223)
        ax3 = plt.subplot(222)
        ax4 = plt.subplot(224)

        plot_max_ampl_distribution(ax1, ch_id, mean_max_ampl_vals, print_text=True,ok_flag=max_ampl_flag)
        plot_max_ampl_summary(ax2, ch_id, mean_max_ampl_vals, print_text=True,ok_flag=max_ampl_flag)
        plot_sigma_max_ampl_distribution(ax3, ch_id, sigma_max_ampl_vals,print_text=True, ok_flag=s_max_ampl_flag)
        plot_sigma_max_ampl_summary(ax4, ch_id, sigma_max_ampl_vals,print_text=True, ok_flag=s_max_ampl_flag)
        plt.tight_layout()
        plt.savefig(outdir+ "13_results_signal_plots.png")#, dpi=dpi)
        
    if pulse_analysis or dac_analysis:
        ### mean wf amplitude from gaussian fit
        plt.clf()
        ax = plt.gca()
        meanwf_ampl_flag = all(flag1)
        title = "Mean wf amplitude"
        xtitle = "Mean wf amplitude (ADC chan)"
        ytitle = "Entries"
        figname="9_meanwf_ampl_distribution"
        mean_ampl,sigma_mean_ampl,_,_= gauss_distribution(ax=ax,data=meanwf_ampl_vals,bins=20,title=title + " distribution",xtitle=xtitle,ytitle=ytitle,dofit=False,figname=figname,outdir=outdir)
        ax.axvline(x=d['mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax.axvline(x=d['mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=meanwf_ampl_flag, x_coord=0.5, y_coord=0.85)        
        plt.savefig(outdir+figname+".png")
        extrafigs.append(outdir+figname+".png")

        plt.clf()
        ax=plt.gca()
        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Channel id")
        #ax.set_xlim(0,64)
        ax.set_ylabel(xtitle)
        figname="10_meanwf_ampl_scatter"
        ax.errorbar(ch_id,meanwf_ampl_vals,yerr=meanwf_ampl_err, marker='o',markersize=4,linestyle=None)
        ax.axhline(y=d['mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=d['mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=meanwf_ampl_flag, x_coord=0.5, y_coord=0.85)
        plt.savefig(outdir+figname +".png")#, dpi=dpi)
        extrafigs.append(outdir+figname+".png")
    if pulse_analysis:
        ### mean wf FWHM from gaussian fit
        plt.clf()
        ax = plt.gca()
        fwhm_flag = all(flag2)
        title = "Mean wf FWHM"
        xtitle = "Mean wf FWHM (ns)"
        ytitle = "Entries"
        figname="11_meanwf_fwhm_distribution"
        mean_ampl,sigma_mean_ampl,_,_= gauss_distribution(ax=ax,data=meanwf_fwhm_vals,bins=20,title=title + " distribution",xtitle=xtitle,ytitle=ytitle,dofit=False,figname=figname,outdir=outdir)
        ax.axvline(x=d['fwhm_mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax.axvline(x=d['fwhm_mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=fwhm_flag, x_coord=0.5, y_coord=0.85)  
        plt.savefig(outdir+figname+".png")
        extrafigs.append(outdir+figname+".png")

        plt.clf()
        ax = plt.gca()
        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Channel id")
        ax.set_ylabel(xtitle)
        figname="12_meanwf_fwhm_scatter"
        ax.errorbar(ch_id,meanwf_fwhm_vals, marker='o',markersize=4,linestyle=None)
        ax.axhline(y=d['fwhm_mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=d['fwhm_mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=fwhm_flag, x_coord=0.5, y_coord=0.85)  
        plt.savefig(outdir+figname+".png")#, dpi=dpi)
        extrafigs.append(outdir+figname+".png")      

        ### mean wf tau from exp fit
        plt.clf()
        ax = plt.gca()
        tau_flag=all(flag3)
        title = "Mean wf tau"
        xtitle = "Mean wf tau (ns)"
        ytitle = "Entries"
        figname="14_meanwf_tau_distribution"
        mean_ampl,sigma_mean_ampl,_,_= gauss_distribution(ax=ax,data=meanwf_tau_vals,bins=20,title=title + " distribution",xtitle=xtitle,ytitle=ytitle,dofit=False,figname=figname,outdir=outdir)
        ax.axvline(x=d['pulse_tau'][0], color='r', linestyle='--', alpha=0.7)
        ax.axvline(x=d['pulse_tau'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=tau_flag, x_coord=0.5, y_coord=0.85)  
        plt.savefig(outdir+figname+".png")
        extrafigs.append(outdir+figname+".png")

        plt.clf()
        ax = plt.gca()
        ch_id=np.arange(minchannel,maxchannel)
        plt.title(title, fontsize=16)
        plt.xlabel("Channel id")
        plt.ylabel(xtitle)
        figname="15_meanwf_tau_scatter"
        plt.errorbar(ch_id,meanwf_tau_vals, marker='o',markersize=4,linestyle=None)
        ax.axhline(y=d['pulse_tau'][0], color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=d['pulse_tau'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax, ok_flag=tau_flag, x_coord=0.5, y_coord=0.85)  
        plt.savefig(outdir+figname+".png")#, dpi=dpi)
        extrafigs.append(outdir+figname+".png")

        ### summary
        plt.clf()
        fig = plt.figure(figsize=(5*3,5*2))
        ax1 = plt.subplot(231)
        ax2 = plt.subplot(234)
        ax3 = plt.subplot(232)
        ax4 = plt.subplot(235)
        ax5 = plt.subplot(233)
        ax6 = plt.subplot(236)

        ### amplitude
        ax1.set_xlabel("Mean wf amplitude (ADC chan)")
        ax1.set_ylabel("Entries")
        ax1.set_title("Mean wf amplitude distribution")
        ax1.hist(meanwf_ampl_vals, bins = 20, range=None, density = False, alpha = 0.75, facecolor='green')
        ax1.axvline(x=d['mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax1.axvline(x=d['mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax1, ok_flag=meanwf_ampl_flag, x_coord=0.5, y_coord=0.85)
        
        ax2.set_xlabel("Channel id")
        ax2.set_ylabel("Mean wf amplitude (ADC chan)")
        ax2.set_title("Mean wf amplitude")        
        ax2.errorbar(ch_id,meanwf_ampl_vals,yerr=meanwf_ampl_err, marker='o',markersize=4,linestyle=None)
        ax2.axhline(y=d['mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax2.axhline(y=d['mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax2, ok_flag=fwhm_flag, x_coord=0.5, y_coord=0.85)

        ### FWHM
        ax3.set_xlabel("Mean wf FWHM (ns)")
        ax3.set_ylabel("Entries")
        ax3.set_title("Mean wf FWHM distribution")
        ax3.hist(meanwf_fwhm_vals, bins = 20, range=None, density = False, alpha = 0.75, facecolor='green')
        ax3.axvline(x=d['fwhm_mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax3.axvline(x=d['fwhm_mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax3, ok_flag=meanwf_ampl_flag, x_coord=0.5, y_coord=0.85)
        
        ax4.set_xlabel("Channel id")
        ax4.set_ylabel("Mean wf FWHM (ns)")
        ax4.set_title("Mean wf FWHM")        
        ax4.errorbar(ch_id,meanwf_fwhm_vals, marker='o',markersize=4,linestyle=None)
        ax4.axhline(y=d['fwhm_mean_ampl_sipm'][0], color='r', linestyle='--', alpha=0.7)
        ax4.axhline(y=d['fwhm_mean_ampl_sipm'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax4, ok_flag=fwhm_flag, x_coord=0.5, y_coord=0.85)

        ### tau
        ax5.set_xlabel("Mean wf tau (ns)")
        ax5.set_ylabel("Entries")
        ax5.set_title("Mean wf tau distribution")
        ax5.hist(meanwf_tau_vals, bins = 20, range=None, density = False, alpha = 0.75, facecolor='green')
        ax5.axvline(x=d['pulse_tau'][0], color='r', linestyle='--', alpha=0.7)
        ax5.axvline(x=d['pulse_tau'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax5, ok_flag=tau_flag, x_coord=0.5, y_coord=0.85)
        
        ax6.set_xlabel("Channel id")
        ax6.set_ylabel("Mean wf tau (ns)")
        ax6.set_title("Mean wf tau")        
        ax6.errorbar(ch_id,meanwf_tau_vals, marker='o',markersize=4,linestyle=None)
        ax6.axhline(y=d['pulse_tau'][0], color='r', linestyle='--', alpha=0.7)
        ax6.axhline(y=d['pulse_tau'][1], color='r', linestyle='--', alpha=0.7)
        print_pass_fail(ax=ax6, ok_flag=tau_flag, x_coord=0.5, y_coord=0.85)

        
        plt.tight_layout()
        plt.savefig(outdir+ "13_results_signal_plots.png")#, dpi=dpi)
        
    '''
    fig = plt.figure(figsize=(5*2,5*2))

    ax1 = plt.subplot(221)
    ax2 = plt.subplot(223)
    ax3 = plt.subplot(222)
    ax4 = plt.subplot(224)

    plot_max_ampl_distribution(ax1, ch_id, mean_max_ampl_vals, print_text=True,
                               ok_flag=max_ampl_flag)
    plot_max_ampl_summary(ax2, ch_id, mean_max_ampl_vals, print_text=True,
                          ok_flag=max_ampl_flag)
    plot_sigma_max_ampl_distribution(ax3, ch_id, sigma_max_ampl_vals,
                                     print_text=True, ok_flag=s_max_ampl_flag)
    plot_sigma_max_ampl_summary(ax4, ch_id, sigma_max_ampl_vals,
                                print_text=True, ok_flag=s_max_ampl_flag)

    #ax1.set_title("max_ampl(mean) distribution")
    #ax1.set_xlabel("max_ampl(mean)")
    ##ax.set_xlim(0,64)
    #ax1.set_ylabel("Entries")
    #ax1.axvline(x=d['max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    #ax1.axvline(x=d['max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    #ax1.hist(mean_max_ampl_vals, bins = 20, density = False, range = None, alpha = 0.75, facecolor='green')

    #ax2.set_title("max_ampl")
    #ax2.set_xlabel("Channel id")
    ##ax.set_xlim(0,64)
    #ax2.set_ylabel("max_ampl(mean)")
    #ax2.errorbar(ch_id,mean_max_ampl_vals, marker='o',markersize=4,linestyle=None)
    #ax2.axhline(y=d['max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    #ax2.axhline(y=d['max_ampl'][1], color='r', linestyle='--', alpha=0.7)

    #ax3.set_title("sigma_max_ampl distribution")
    #ax3.set_xlabel("sigma_max_ampl")
    ##ax.set_xlim(0,64)
    #ax3.set_ylabel("Entries")
    #ax3.axvline(x=d['sigma_max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    #ax3.axvline(x=d['sigma_max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    #ax3.hist(sigma_max_ampl_vals, bins = 20, density = False, range = None, alpha = 0.75, facecolor='green')

    #ax4.set_title("sigma_max_ampl")
    #ax4.set_xlabel("Channel id")
    ##ax.set_xlim(0,64)
    #ax4.set_ylabel("sigma_max_ampl")
    #ax4.errorbar(ch_id,sigma_max_ampl_vals, marker='o',markersize=4,linestyle=None)
    #ax4.axhline(y=d['sigma_max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    #ax4.axhline(y=d['sigma_max_ampl'][1], color='r', linestyle='--', alpha=0.7)

    plt.tight_layout()

    plt.savefig(outdir+ "13_results_signal_plots.png")#, dpi=dpi)
    '''
    
    time_diffs = {}
    if do_timediff:
        logger.info("Calculating time difference")
        for chan in range(minchannel,maxchannel):
            asic = int(chan/16)
            if asic not in time_diffs.keys():
                time_diffs[asic]={}
            for chan1 in range(minchannel,maxchannel):
                logger.info("Running channel " +str(chan)+ " vs channel " +str(chan1))
                if int(chan1/16)==asic:
                    c0 = chan%16
                    c1 = chan1%16

                    title = "Time difference - channel %i vs %i%s"%(chan,chan1,tag)
                    title1 = "Time difference1 - channel %i vs %i%s"%(chan,chan1,tag)
                    xtitle="Time (ns)"
                    ytitle="Entries"
                    figname= '14_Time_difference_channel%i_vs_%i%s'%(chan,chan1,tag)
                    figname1= '14_Time_difference1_channel%i_vs_%i%s'%(chan,chan1,tag)

                    datamax0=np.max(wf_cal.waveforms[:,chan,:], axis=1)
                    datamax1=np.max(wf_cal.waveforms[:,chan1,:], axis=1)

                    wfs0 = wf_cal.waveforms[:,chan,:].tolist()
                    wfs1 = wf_cal.waveforms[:,chan1,:].tolist()
                    a = wf_cal.waveforms[:,chan,:].tolist()
                    time_of_max0 = []
                    time_of_max1 = []
                    time_of_hmax0 = []
                    time_of_hmax1 = []
                    dt = []
                    dt1 = []
                    for i in range(len(datamax0)-1):
                        #if i==578: # and (chan==16 or chan1==16):
                        #    continue
                        time_of_max0.append(wfs0[i].index(datamax0[i]))
                        time_of_max1.append(wfs1[i].index(datamax1[i]))
                        #logger.info("chan = " + str(chan) + " chan1 = " + str(chan1) + str(i) + " " + str(len(datamax0) + " " + str(len(datamax0[i]/2)) + " " + wfs0[i])
                        time_of_hmax0.append( float(np.interp( datamax0[i]/2, wfs0[i][:time_of_max0[-1]], np.arange(time_of_max0[-1]) )) )
                        time_of_hmax1.append( float(np.interp( datamax1[i]/2, wfs1[i][:time_of_max1[-1]], np.arange(time_of_max1[-1]) )) )
                        dt.append(time_of_max0[-1]-time_of_max1[-1])
                        dt1.append(time_of_hmax0[-1]-time_of_hmax1[-1])

                    dt = np.array(dt).astype(np.float32)
                    dt1 = np.array(dt1).astype(np.float32)
                    logger.debug("dt = " + str(dt) + ", dt1 " + str(dt1))

                    ax=plt.gca()
                    mean_dt, sigma_dt, _tmp1, _tmp2 = \
                        gauss_distribution(
                            ax=ax,
                            data=dt,
                            bins=50,
                            title=title,
                            xtitle=xtitle,
                            ytitle=ytitle,
                            dofit=False,
                            figname=figname,
                            outdir=outdir,
                            ylog=False
                        )
                    plt.savefig(outdir+figname+".png")
                    mean_dt1, sigma_dt1, _tmp1, _tmp2 = \
                        gauss_distribution(
                            ax=ax,
                            data=dt1,
                            bins=50,
                            title=title1,
                            xtitle=xtitle,
                            ytitle=ytitle,
                            dofit=True,
                            figname=figname1,
                            outdir=outdir,
                            ylog=False
                        )
                    plt.savefig(outdir+figname1+".png")


                    time_diffs[asic][str(c0)+"_"+str(c1)] = [float(mean_dt), float(sigma_dt),float(mean_dt1), float(sigma_dt1)]
            logger.debug("time diffs = " + str(time_diffs))


        yaml.dump(time_diffs, timediff_file, default_flow_style=False)

    if do_ct:
        for sig_ch in signal_ch_list:
            asic = int(sig_ch/16)
            ct_file.write(str(sig_ch))
            for ch in range(asic*16, (asic+1)*16):
                cross_talk = (mean_amplitude[ch]/mean_amplitude[sig_ch])
                logger.debug( "cross talk = " + str(cross_talk))
                ct_file.write('\t' + str(cross_talk))
            ct_file.write('\n')

        ct_file.close()

    #for figname in figname_list:
    #    plots_canvas(figname,tag,outdir,minchannel,maxchannel)
    #plots_to_pdf(figname_list,tag,outdir,"results_signal_plots.pdf",minchannel,maxchannel, extrafigs=extrafigs)


    if fname_r0 is not None:
        del wf_0
    del wf_cal

    logger.log(logger.TEST_LEVEL_INFO,"Finished signal analysis.")

    return nbad_ch

def analyse_triggerscan(fname_list, n=4, outdir="./",limitsdir="./",
                        fname_limits="limits.yaml",target_hz=None,
                        g0=0,ng=16,tag=""):
    """
    Parameters
    ----------
    fname_list : list_like
                 List containing names of the yaml files where the scan params
                 and measured rates are stored
    n : integer
        number a consecutive points that define a plateau
        e.g.: if n = 3, every sequence of at least 3 "stable" points is
        identified as plateau
    outdir: output analysis folder
    limitsdir: folder containing the limits.yaml file
    fname_limits: name of file containing limits
    target_hz: frequency injected by the pulser during data taking
    g0: starting group for analysis
    ng: number of groups to analyse
    Returns
    ----------
    """
    logger.log(logger.TEST_LEVEL_INFO, "Starting triggerscan analysis...")
    dpi=100

    if tag!="" and not tag.startswith("_"):
        tag ="_"+tag

    gmax=g0+ng

    n = int(n)

    with open(limitsdir+fname_limits) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)

    plateau_start_list = [d['plateau_start'][0],d['plateau_start'][1]]
    plateau_width_list = [d['plateau_width'][0],d['plateau_width'][1]]
    plateau_height_list = [d['plateau_height'][0],d['plateau_height'][1]]
    plateau_height_std_list = [d['plateau_height_std'][0],d['plateau_height_std'][1]]

    peak_pos_list = [d['peak_pos'][0],d['peak_pos'][1]]
    peak_width_list = [d['peak_width'][0],d['peak_width'][1]]
    peak_height_list = [d['peak_height'][0],d['peak_height'][1]]
    peak_plateau_dist_list = [d['peak_plateau_dist'][0],d['peak_plateau_dist'][1]]

    group_list = [d['group'][0],d['group'][1]]
    group_list += list(range(g0,gmax))

    #print(group_list)

    manager = enlighten.get_manager()

    pbar = manager.counter(total=len(range(g0,gmax)), leave = False)

    for fname in fname_list:

        #print(fname)

        with open(fname) as fptr:
            # d = yaml.load(fptr, Loader=yaml.FullLoader)
            d = yaml.load(fptr, Loader=yaml.Loader)

        pmtref4_vec = d["pmtref4"]
        thresh_vec = d["thresh"]
        rates = d["rates"]
        #trigger_duration = d["trigger_duration"]
        title = fname.split("/")[-1].split(".")[0]
        #print(title)

        #check from dataset whether scan over pmtref4 or thresh
        #a_scan is the array containing the values of the scanning
        #parameter
        if pmtref4_vec == None:
            label = "thresh"
            a_scan = np.array(thresh_vec,dtype=float)

        if thresh_vec == None:
            label = "pmtref4"
            a_scan = np.array(pmtref4_vec,dtype=float)

        a_rates = np.array(rates,dtype=float)

        #1 - mask for rates > 0
        mask_0 = a_rates>0.

        a_rates_mask_0 = a_rates[mask_0]
        a_scan_mask_0 = a_scan[mask_0]

        if(len(a_rates_mask_0)==len(a_scan_mask_0)==0):
            plateau_start_list.append("{0}".format(-1))
            plateau_width_list.append("{0}".format(-1))
            plateau_height_list.append("{0}".format(-1))
            plateau_height_std_list.append("{0}".format(-1))

            peak_pos_list.append("{0}".format(-1))
            peak_width_list.append("{0}".format(-1))
            peak_height_list.append("{0}".format(-1))
            peak_plateau_dist_list.append("{0}".format(-1))
            continue

        #2 - peak search and fit
        rate_peak = np.max(a_rates_mask_0)
        pos_peak = np.argmax(a_rates_mask_0)
        scan_pos_peak = a_scan_mask_0[pos_peak]

        #choose as fit interval for the peak, all points above
        #a fixed percentage of the peak (scan_thresh)
        #if there are less than 3 points in a_rates peak_fit
        #--> take interval around +-2 points on left and right
        #NOTE: If the peak has a low height, the points above scan_thresh
        #could be all the non-zero rates. If this happens, when searching for plateau,
        #the search range (e.g.: for pmtref4) would include only the very last point of the plateau.
        #For this reason, a robust fallback solution is to consider directly +-2 points around the peak.

        """
        scan_thresh = 0.02
        a_rates_peak_fit = a_rates_mask_0[a_rates_mask_0>=scan_thresh*rate_peak]
        a_scan_peak_fit = a_scan_mask_0[a_rates_mask_0>=scan_thresh*rate_peak]

        if (len(a_rates_peak_fit)<4):
        """
        a_rates_peak_fit = a_rates_mask_0[pos_peak-2:pos_peak+3]
        a_scan_peak_fit = a_scan_mask_0[pos_peak-2:pos_peak+3]

        #there could be cases where there are not enough points at the
        #right or the left of the peak. Take peak position and height
        #from rate_peak and scan_pos_peak

        if(len(a_rates_peak_fit)==len(a_scan_peak_fit)<=2):
            #for the fit there ought to be at least 3 points
            #(number of dof of the fit)
            a_rates_peak_fit = np.array([a_rates_mask_0[pos_peak]])
            a_scan_peak_fit = np.array([a_scan_mask_0[pos_peak]])
            A, mu, sigma = rate_peak, scan_pos_peak, 0.
            x_fit = np.array([])
            y_fit = np.array([])

        else:
            #gaus_function(x,A,mu,sigma)
            p0 = [rate_peak, scan_pos_peak, (a_scan_peak_fit[-1]-a_scan_peak_fit[0])/2]
            popt, pcov = curve_fit(gaus_function, a_scan_peak_fit, a_rates_peak_fit, p0=p0)
            #print(popt)

            step = a_scan_peak_fit[1]-a_scan_peak_fit[0]
            x_fit = np.arange(a_scan_peak_fit[0],a_scan_peak_fit[-1]+step,1)
            A,mu,sigma = popt[0],popt[1],popt[2]
            y_fit = gaus_function(x_fit,A,mu,sigma)
        fwhm = 2*np.sqrt(2*np.log(2)) * sigma

        #3 - find plateau

        #3a
        #restrict search to rate points at the right of the peak (pmtref4 scan)
        #or at the left of the peak (thresh scan)

        if pmtref4_vec == None:
            #this is a thresh scan:
            #plateau search will be from the beginning of the array
            #up to the first point of the peak fit interval
            a_rates_mask_0_plateau = a_rates_mask_0[a_scan_mask_0<=a_scan_peak_fit[0]]
            a_scan_mask_0_plateau = a_scan_mask_0[a_scan_mask_0<=a_scan_peak_fit[0]]

        if thresh_vec == None:
            #this is a pmtref4 scan:
            #plateau search will be from the the last point of the peak fit interval
            #up to the end of the array
            a_rates_mask_0_plateau = a_rates_mask_0[a_scan_mask_0>=a_scan_peak_fit[-1]]
            a_scan_mask_0_plateau = a_scan_mask_0[a_scan_mask_0>=a_scan_peak_fit[-1]]

        #add check to see if length of plateau search array is at least n
        #(number of points that define a plateau)
        #if not, append -1
        if(len(a_rates_mask_0_plateau)==len(a_scan_mask_0_plateau)<n):
            plateau_start_list.append("{0}".format(-1))
            plateau_width_list.append("{0}".format(-1))
            plateau_height_list.append("{0}".format(-1))
            plateau_height_std_list.append("{0}".format(-1))
            peak_plateau_dist_list.append("{0}".format(-1))
            plateau_start=-1

        else:
            #3b - relative variation
            a_rates_rel = var_rel(a_rates_mask_0_plateau)
            #drop first element also in thresh/pmtref4 array
            #--> relative variation not defined
            a_scan_rel = a_scan_mask_0_plateau[1:]

            #select points that have relative variation within an arbitrary limit
            #(boolean) mask_1: |var_rel(y)| < a_rates_rel_thresh_0

            a_rates_rel_thresh_0 = 1e-2

            mask_1 = np.abs(a_rates_rel)<a_rates_rel_thresh_0
            a_scan_rel_mask_1 = a_scan_rel[mask_1]
            a_rates_rel_mask_1 = a_rates_rel[mask_1]

            #3c - identify plateaux
            #check groups of consecutive True in mask_1

            groups = []
            uniquekeys = []
            len_groups = []
            for k, g in groupby(mask_1):
                group = list(g)
                groups.append(group)
                len_groups.append(len(group))
                uniquekeys.append(k)

            #make a list of pmtref4/thresh values and corresponding var_rel
            #that satisfy the "n" requirement --> "n-1" for var_rel array

            n_rel = n-1

            list_plateau_scan_rel = []
            list_plateau_rates_rel = []

            for i,len_group in enumerate(len_groups):
                if(uniquekeys[i]==True):
                    if(len_group>=n_rel):
                        pos_start_plateau_rel = sum(len_groups[:i])
                        pos_end_plateau_rel = pos_start_plateau_rel+len_groups[i]
                        list_plateau_scan_rel.append(a_scan_rel[pos_start_plateau_rel:pos_end_plateau_rel])
                        list_plateau_rates_rel.append(a_rates_rel[pos_start_plateau_rel:pos_end_plateau_rel])

            a_plateau_scan_rel = np.array(list_plateau_scan_rel)
            a_plateau_rates_rel = np.array(list_plateau_rates_rel)

            #switch to rates array
            list_plateau_scan = []
            list_plateau_rates = []

            for i in range(len(a_plateau_scan_rel)):
                pos_start_plateau = np.where(a_scan_mask_0==a_plateau_scan_rel[i][0])[0][0] - 1
                pos_end_plateau = pos_start_plateau + len(a_plateau_scan_rel[i]) + 1
                list_plateau_scan.append(a_scan_mask_0[pos_start_plateau:pos_end_plateau])
                list_plateau_rates.append(a_rates_mask_0[pos_start_plateau:pos_end_plateau])

            a_plateau_scan = np.array(list_plateau_scan)
            a_plateau_rates = np.array(list_plateau_rates)

            #calculate quality check parameters for plateau
            #note: at the moment the plateau_start and plateau_end
            #are the edges of the a_plateau_scan found with the previous method
            #under the assumption of one plateau only with minor fluctuations

            try:
                plateau_start = np.where(a_scan_mask_0==a_plateau_scan[0][0])[0][0]
                plateau_end = np.where(a_scan_mask_0==a_plateau_scan[-1][-1])[0][0]

                plateau_height = np.mean(a_rates_mask_0[plateau_start:plateau_end+1])
                plateau_height_std = np.std(a_rates_mask_0[plateau_start:plateau_end+1])
                plateau_width = a_scan_mask_0[plateau_end] - a_scan_mask_0[plateau_start]
            except:
                plateau_start = -1
                plateau_end = -1
                plateau_height = -1
                plateau_height_std = -1
                plateau_width = -1
            #calculate peak_plateau_dist to quantify noise level along with
            #fwhm

            if pmtref4_vec == None:
                #this is a thresh scan - peak is on the right, plateau on the left
                peak_plateau_dist = (mu - 3*sigma) - a_scan_mask_0[plateau_end]

            if thresh_vec == None:
                #this is a pmtref4 scan - peak is on the left, plateau on the right
                peak_plateau_dist = a_scan_mask_0[plateau_start] - (mu + 3*sigma)

            #print("plateau_start: {0:d}".format(int(a_scan_mask_0[plateau_start])))
            #print("plateau_width: {0:d}".format(int(plateau_width)))
            #print("plateau_height: {0:.2f}".format(plateau_height))
            #print("plateau_height_std: {0:.2f}".format(plateau_height_std))

            #print("peak_pos: {0:.2f}".format(mu))
            #print("peak_width: {0:.2f}".format(fwhm))
            #print("peak_height: {0:.2f}".format(A))
            #print("peak_plateau_dist: {0:.2f}".format(peak_plateau_dist))

            plateau_start_list.append("{0:d}".format(int(a_scan_mask_0[plateau_start])))
            plateau_width_list.append("{0:d}".format(int(plateau_width)))
            plateau_height_list.append("{0:.2f}".format(plateau_height))
            plateau_height_std_list.append("{0:.2f}".format(plateau_height_std))
            peak_plateau_dist_list.append("{0:.2f}".format(peak_plateau_dist))

        peak_pos_list.append("{0:.2f}".format(mu))
        peak_width_list.append("{0:.2f}".format(fwhm))
        peak_height_list.append("{0:.2f}".format(A))

        #summary plot for analysed group
        fig = plt.figure(figsize=(20,10))
        ax0 = plt.subplot(1,1,1)
        ax0.set_ylim(1,1e8)
        ax0.set_xticks(a_scan_mask_0, minor=True)
        ax0.tick_params(axis='x', which='major', direction='out', length=10., width=3., labelsize=18)
        ax0.tick_params(axis='x', which='minor', direction='out', length=5., width=1.5, labelsize=18)
        ax0.tick_params(axis='y', which='major', direction='out', length=10., width=3., labelsize=18)
        ax0.grid(which='major', axis='x', color='k', linestyle='-', linewidth=1., alpha=0.5)
        ax0.grid(which='minor', axis='x', color='k', linestyle='--', linewidth=1., alpha=0.2)
        ax0.set_yscale("log")
        ax0.set_ylabel(r"rates ($\mathrm{Hz}$)", size=20)
        ax0.set_xlabel(r"{0}".format(label), size=20)
        ax0.set_title(title,fontsize=24)
        ax0.plot(a_scan_mask_0,a_rates_mask_0,'bo-')

        ax0.plot(a_scan_peak_fit, a_rates_peak_fit, 'o', color='magenta', linewidth=0)
        ax0.plot(x_fit, y_fit, linestyle='dashed', color='magenta', linewidth=1)

        if(plateau_start==-1): #check if variable plateau_start is -1 --> case in which plateau is not defined
            ax0.text(0.3, 0.25, 'plateau: n.d.',
                         color = 'orange' , fontsize = 24,
                         horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)

        else:
            ax0.text(0.3, 0.25, 'plateau_start: {0:d}'.format(int(a_scan_mask_0[plateau_start])),
                     color = 'orange' , fontsize = 24,
                     horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
            ax0.text(0.3, 0.20, 'plateau_width: {0:d}'.format(int(plateau_width)),
                 color = 'orange' , fontsize = 24,
                 horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
            ax0.text(0.3, 0.15, 'plateau_height: {0:.2f} {1}'.format(plateau_height,"Hz"),
                         color = 'orange' , fontsize = 24,
                         horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
            ax0.text(0.3, 0.10, 'plateau_height_std: {0:.2f} {1}'.format(plateau_height_std,"Hz"),
                         color = 'orange' , fontsize = 24,
                         horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
            ax0.text(0.3, 0.80, 'peak_plateau_distance: {0:.2e}'.format(peak_plateau_dist),
                 color = 'black' , fontsize = 24,
                 horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
            ax0.plot(a_scan_mask_0[plateau_start:plateau_end+1],
                     a_rates_mask_0[plateau_start:plateau_end+1],marker='o',color='orange')
            if pmtref4_vec == None:
                #this is a thresh scan - peak is on the right, plateau on the left
                ax0.axvline(a_scan_mask_0[plateau_end],linestyle='-',linewidth='3',color='black')
                ax0.axvline((mu - 3*sigma),linestyle='-',linewidth='3',color='black')

            if thresh_vec == None:
                #this is a pmtref4 scan - peak is on the left, plateau on the right
                ax0.axvline(a_scan_mask_0[plateau_start],linestyle='-',linewidth='3',color='black')
                ax0.axvline((mu + 3*sigma),linestyle='-',linewidth='3',color='black')

            ax1 = ax0.twinx()
            ax1.set_ylim(-0.5,0.5)
            ax1.plot(a_scan_rel,a_rates_rel,'ro')
            ax1.plot(a_scan_rel_mask_1,a_rates_rel_mask_1,'go')
            ax1.tick_params(axis='y', which='major', direction='out', length=10., width=3., labelsize=18)
            ax1.axhline(a_rates_rel_thresh_0,linestyle='--',linewidth='3',color='red')
            ax1.axhline(-1*a_rates_rel_thresh_0,linestyle='--',linewidth='3',color='red')

        ax0.text(0.3, 0.95, 'peak_pos: {0:.2f}'.format(mu),
                     color = 'magenta' , fontsize = 24,
                     horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
        ax0.text(0.3, 0.90, 'peak_height: {0:.2f} {1}'.format(A,"Hz"),
                     color = 'magenta' , fontsize = 24,
                     horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)
        ax0.text(0.3, 0.85, 'peak_width: {0:.2f}'.format(fwhm),
                 color = 'magenta' , fontsize = 24,
                 horizontalalignment='left', verticalalignment='center', transform=ax0.transAxes)

        fig.savefig(outdir+"{0}.png".format(title))

        pbar.update()

    pbar.close()
    manager.stop()

    logger.log(logger.TEST_LEVEL_INFO, "Write triggerscan results file...")

    #print(len(group_list))
    #print(len(plateau_start_list))
    #print(len(peak_plateau_dist_list))

    #### OLD txt files -- commented -- CHECK the try/except block
    #try:
    #    df_results = pd.DataFrame({'#Group':group_list,
    #                   'plateau_start':plateau_start_list,
    #                   'plateau_width':plateau_width_list,
    #                   'plateau_height':plateau_height_list,
    #                   'plateau_height_std':plateau_height_std_list,
    #                   'peak_pos':peak_pos_list,
    #                   'peak_width':peak_width_list,
    #                   'peak_height':peak_height_list,
    #                   'peak_plateau_dist':peak_plateau_dist_list})
    #except ValueError as v:
    #    custom_message = "check group 0 (-g0)  or number of groups (-ng)"
    #    logger.exception("{0}: {1}".format(str(v), custom_message))
    #    logger.log(logger.TEST_LEVEL_FAIL, "{0}: {1}".format(str(v), custom_message))
    #    exit(1)

    #fname_results = "results_{0}_scan.txt".format(label)
    #df_results.to_csv(outdir+fname_results,
    #                  sep='\t',index=False)


    #print(plateau_start_list)
    #print(peak_pos_list)

    columns = ['group', 'plateau_start','plateau_width','plateau_height','plateau_height_std',
               'peak_pos','peak_width', 'peak_height', 'peak_plateau_dist']
    types = ['int32','float32','float32','float32','float32','float32','float32','float32', 'float32']
    trig_output = MyOutput(columns=columns).set_types(types)
    trig_output['group'] = group_list[2:]
    trig_output['plateau_start'] = plateau_start_list[2:]
    trig_output['plateau_width'] = plateau_width_list[2:]
    trig_output['plateau_height'] = plateau_height_list[2:]
    trig_output['plateau_height_std'] = plateau_height_std_list[2:]
    trig_output['peak_pos'] = peak_pos_list[2:]
    trig_output['peak_width'] = peak_width_list[2:]
    trig_output['peak_height'] = peak_height_list[2:]
    trig_output['peak_plateau_dist'] = peak_plateau_dist_list[2:]

    fname_results = "results_{0}_scan".format(label)
    trig_output.save_to_file(outdir+ fname_results+"2.txt", sep=";")
    trig_output = MyOutput(data=pd.read_csv(outdir+ fname_results+"2.txt",
                                           header=0, sep=";"))
    trig_output.add_limits_to_output(mode=output_results_mode)

    # Check quality on trig_output for all parameters
    flag1 = trig_output.check_quality("plateau_start")
    flag2 = trig_output.check_quality("plateau_width")
    flag3 = trig_output.check_quality("plateau_height")
    flag4 = trig_output.check_quality("plateau_height_std")
    flag5 = trig_output.check_quality("peak_pos")
    flag6 = trig_output.check_quality("peak_width")
    flag7 = trig_output.check_quality("peak_height")
    flag8 = trig_output.check_quality("peak_plateau_dist")
    #flags=[flag1.all(),flag2.all(),flag3.all(),flag4.all(),flag5.all(),flag6.all(),flag7.all(),flag8.all()]
    flags=[flag1,flag2,flag3,flag4,flag5,flag6,flag7,flag8]
    # Get number of bad channels
    nbad_ch = np.logical_not(flag1*flag2*flag3*flag4*flag5*flag6*flag7*flag8).sum()


    trig_output.save_to_html(outdir+ fname_results+".html")
    trig_output.save_to_file(outdir+ fname_results+".txt", sep="\t", align_colnames=True)



    #produce summary plots
    logger.log(logger.TEST_LEVEL_INFO, "Triggerscan summary plots...")

    fig1, ax1 = plt.subplots(1)
    fig2, ax2 = plt.subplots(1)
    fig3, ax3 = plt.subplots(1)
    fig4, ax4 = plt.subplots(1)
    fig5, ax5 = plt.subplots(1)
    fig6, ax6 = plt.subplots(1)
    fig7, ax7 = plt.subplots(1)
    fig8, ax8 = plt.subplots(1)
    fig9, ax9 = plt.subplots(1)
    fig10, ax10 = plt.subplots(1)
    fig11, ax11 = plt.subplots(1)
    fig12, ax12 = plt.subplots(1)
    fig13, ax13 = plt.subplots(1)
    fig14, ax14 = plt.subplots(1)
    fig15, ax15 = plt.subplots(1)
    fig16, ax16 = plt.subplots(1)

    plot_triggerscan_summary(outdir+fname_results+".txt",
                             ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8,
                             ax9,ax10,ax11,ax12,ax13,ax14,ax15,ax16,
                             target_hz=target_hz,
                             group_list=list(range(g0,gmax)), flags=flags)

    fig1.savefig(outdir+"{0}_plateau_start_distribution.png".format(label))
    fig2.savefig(outdir+"{0}_plateau_width_distribution.png".format(label))
    fig3.savefig(outdir+"{0}_plateau_height_distribution.png".format(label))
    fig4.savefig(outdir+"{0}_plateau_height_std_distribution.png".format(label))
    fig5.savefig(outdir+"{0}_plateau_start_vs_group.png".format(label))
    fig6.savefig(outdir+"{0}_plateau_width_vs_group.png".format(label))
    fig7.savefig(outdir+"{0}_plateau_height_vs_group.png".format(label))
    fig8.savefig(outdir+"{0}_plateau_height_std_vs_group.png".format(label))

    fig9.savefig(outdir+"{0}_peak_pos_distribution.png".format(label))
    fig10.savefig(outdir+"{0}_peak_width_distribution.png".format(label))
    fig11.savefig(outdir+"{0}_peak_height_distribution.png".format(label))
    fig12.savefig(outdir+"{0}_peak_plateau_dist_distribution.png".format(label))
    fig13.savefig(outdir+"{0}_peak_pos_vs_group.png".format(label))
    fig14.savefig(outdir+"{0}_peak_width_vs_group.png".format(label))
    fig15.savefig(outdir+"{0}_peak_height_vs_group.png".format(label))
    fig16.savefig(outdir+"{0}_peak_plateau_dist_vs_group.png".format(label))

    ax1.cla()
    ax2.cla()
    ax3.cla()
    ax4.cla()
    ax5.cla()
    ax6.cla()
    ax7.cla()
    ax8.cla()
    ax9.cla()
    ax10.cla()
    ax11.cla()
    ax12.cla()
    ax13.cla()
    ax14.cla()
    ax15.cla()
    ax16.cla()

    fig1 = plt.figure(figsize=(4*2,4*2))
    ax1 = plt.subplot(421)
    ax2 = plt.subplot(422)
    ax3 = plt.subplot(423)
    ax4 = plt.subplot(424)
    ax5 = plt.subplot(425)
    ax6 = plt.subplot(426)
    ax7 = plt.subplot(427)
    ax8 = plt.subplot(428)

    fig2 = plt.figure(figsize=(4*2,4*2))
    ax9 = plt.subplot(421)
    ax10 = plt.subplot(422)
    ax11 = plt.subplot(423)
    ax12 = plt.subplot(424)
    ax13 = plt.subplot(425)
    ax14 = plt.subplot(426)
    ax15 = plt.subplot(427)
    ax16 = plt.subplot(428)

    plot_triggerscan_summary(outdir+fname_results+".txt",
                             ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8,
                             ax9,ax10,ax11,ax12,ax13,ax14,ax15,ax16,
                             target_hz=target_hz,
                             group_list=list(range(g0,gmax)), flags=flags)

    fig1.tight_layout()
    fig1.savefig(outdir+"{0}_scan_plateau_summary.png".format(label))
    fig2.tight_layout()
    fig2.savefig(outdir+"{0}_scan_peak_summary.png".format(label))

    ax1.cla()
    ax2.cla()
    ax3.cla()
    ax4.cla()
    ax5.cla()
    ax6.cla()
    ax7.cla()
    ax8.cla()
    ax9.cla()
    ax10.cla()
    ax11.cla()
    ax12.cla()
    ax13.cla()
    ax14.cla()
    ax15.cla()
    ax16.cla()

    return nbad_ch


def do_signal_plots(filenames,ampl_list, outdir, chlist=None):
    data_dict = {}
    '''
    for filename, sig in zip(filenames,ampl_list):
        amplitude = sig
        data_dict["Signal_amplitude{0:.4f}".format(amplitude)]={}
        #filename = "plots/signal_exttrigger_signal"+sig+"_nblocks4_packets4_vped1200_delaaml500/results_signal_"+str(amplitude)+ ".txt"
        #filename = filename_in.format(sig)
        logger.debug("filename = " + filename)
        data_file = open(filename,"r")
        x = data_file.read()
        lines = x.split('\n')
        lines=lines[1:]
        #for ich,ch in enumerate(range(asic0*16,asic0*16+len(lines)-2)):
        for _line in lines:
            line = _line.split('\t')
            ch = int(line[0])
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]={}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Max_amplitude"]={"Value":float(line[1]),"Sigma":float(line[2])}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Time_of_max_amplitude"]={"Value":float(line[3]),"Sigma":float(line[4])}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Time_of_max_from_wf"]={"Value":float(line[5]),"Sigma":float(line[6])}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Amplitude_fixed_time"]={"Value":float(line[7]),"Sigma":float(line[8])}
        data_file.close()
    '''
    for filename, amplitude in zip(filenames,ampl_list):
        #filename="plots/pedestal_exttrigger_nblocks4_packets4_vped"+str(vped)+"_delay500_r0/results_pedestal.txt"
        #filename=filename_ped%(vped)
        filename_res = filename.replace("_r0.tio","")+"/results_signal2.txt"
        myout = MyOutput(data=pd.read_csv(filename_res, header=0, sep=";"))
        ## columns = ['Channel', 'Max_ampl','Sigma_max_ampl','Time_of_max','Sigma_time_of_max','Time_of_max_wf','Sigma_time_of_max_wf','Mean_ampl_fixed_t','Sigma_ampl_fixed_t']
        data_dict["Signal_amplitude{0:.4f}".format(amplitude)]={}
        channel_list = []
        for ch in myout.ch:
            ch = int(ch)
            channel_list.append(ch)

            row = myout.loc[myout.ch==ch]
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]={}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Max_amplitude"]={"Value": row["max_ampl"].values[0],"Sigma": row["sigma_max_ampl"].values[0]}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Time_of_max_amplitude"]={"Value":row["tmaximum"].values[0],"Sigma":row["sigma_tmax"].values[0]}
            data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Time_of_max_from_wf"]={"Value":row["tmaximum_wf"].values[0],"Sigma":row["sigma_tmax_wf"].values[0]}
            #******** ##data_dict["Signal_amplitude{0:.4f}".format(amplitude)]["Channel"+str(ch)]["Amplitude_fixed_time"]={"Value":row["Mean_ampl_fixed_t"].values[0],"Sigma":row["Sigma_ampl_fixed_t"].values[0]}

    logger.log(logger.TEST_LEVEL_MESS,"channels: {0}".format(len(myout.ch)))
    summary_filename = outdir+ "/summary_results_signal.txt"
    #summary_file = open(summary_filename,"w")
    #summary_file.write('Channel\tADC_Gain\tADC_Gain_1\tADC_Gain_2\n')

    #columns = ['Channel', 'ADC_Gain_m', 'ADC_Gain_q','ADC_Gain_1_m','ADC_Gain_1_q', 'ADC_Gain_2_m','ADC_Gain_2_q'] ## for fit in two ranges
    #types = ['int32','float32','float32','float32','float32','float32','float32']
    columns = ['Channel', 'ADC_Gain_m', 'ADC_Gain_q']
    types = ['int32','float32','float32']
    summary_output = MyOutput(columns=columns).set_types(types)

    ### Performing amplitude in ADC vs amplitude of input signal ###
    slopes=[]
    slopes1=[]
    slopes2=[]
    #plt.figure()
    #ax = plt.subplot(111)
    colors=get_colors(16)
    my_col = get_col_map(colors)

    #nasics = len(myout.ch) // 16
    #if (len(myout.ch)%16 != 0):
    #    nasics+=1

    #logger.log(logger.TEST_LEVEL_MESS,"nasics: {0}".format(nasics))
    if chlist is not None:
        channel_list = chlist

    for chan in channel_list:
    #for asic in range(nasics):
        asic = int(chan/16)
        ch = chan%16
        bad_ch=[]
        #plt.xlabel("Amplitude of input signal (Volts@Func.Gen.)")
        #plt.ylabel("Amplitude of digital signal (ADC units)")
        #adc_values = []

        #for ch in range(16):
        #    chan = ch + asic*16
        #    if chan not in myout.ch:
        #        #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
        #        break
        if chan not in summary_output["Channel"].tolist():
            summary_output.loc[len(summary_output),"Channel"]=chan
        y_value = []
        y_value_err = []
        x_value = []
        x_value_fit1 = []
        y_value_fit1 = []
        y_value_fit1_err = []
        x_value_fit2 = []
        y_value_fit2 = []
        y_value_fit2_err = []

        for x in ampl_list:
            amplitude = x
            x_value.append(amplitude)
            #logger.info("asic: {}, ch: {}, x: {}".format(asic,ch,x) + str(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).keys()))

            #y_value.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Value"))
            #y_value_err.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Sigma"))
            #y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Value"))
            #y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Sigma"))
            y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
            y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
            if y_value[-1]<=500:
                x_value_fit1.append(x_value[-1])
                y_value_fit1.append(y_value[-1])
                y_value_fit1_err.append(y_value_err[-1])
            else:
                x_value_fit2.append(x_value[-1])
                y_value_fit2.append(y_value[-1])
                y_value_fit2_err.append(y_value_err[-1])

        x_value = np.array(x_value)
        color=my_col[ch]
        x_value_fit1 = np.array(x_value_fit1)
        y_value_fit1 = np.array(y_value_fit1)
        y_value_fit1_err = np.array(y_value_fit1_err)

        x_value_fit2 = np.array(x_value_fit2)
        y_value_fit2 = np.array(y_value_fit2)
        y_value_fit2_err = np.array(y_value_fit2_err)

        a,b,r,p,e = stats.linregress(ampl_list,y_value)
        slopes.append(a)
        #a1,b1,r1,p1,e1 = stats.linregress(x_value_fit1,y_value_fit1)
        a1,b1 = a,b
        slopes1.append(a1)
        #a2,b2,r2,p2,e2 = stats.linregress(x_value_fit2,y_value_fit2)
        a2,b2=a,b
        slopes2.append(a2)

        ##plt.errorbar(x = x_value, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        #plt.errorbar(x = x_value, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(chan))
        ##plt.plot(x_value, a*x_value+b, linestyle='--', color=color)
        #plt.plot(x_value_fit1, a1*x_value_fit1+b1, linestyle='--', color=color)
        #plt.plot(x_value_fit2, a2*x_value_fit2+b2, linestyle='--', color=color)
        #adc_values.append(y_value)
        summary_output.loc[summary_output.Channel==chan, "ADC_Gain_m"] = a
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_1_m"] = a1
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_2_m"] = a2
        summary_output.loc[summary_output.Channel==chan, "ADC_Gain_q"] = b
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_1_q"] = b1
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_2_q"] = b2

        #flag = summary_output.check_quality("ADC_Gain_m", rows=len(summary_output)-1)
        #flag1 = summary_output.check_quality("ADC_Gain_1_m", rows=len(summary_output)-1)
        #flag2 = summary_output.check_quality("ADC_Gain_2_m", rows=len(summary_output)-1)
        #logger.debug("Flag for ADC_Gain on channel "+str(chan)+" is: " +str(flag))
        #logger.debug("Flag for ADC_Gain from fit in two ranges on channel "+str(chan)+" is: " +str(flag1 & flag2))
        #if not flag:
        #    #if not flag1 & flag2:
        #    bad_ch.append(str(chan))
        ##logger.log(logger.TEST_LEVEL_MESS,"rows: {0}".format(range(asic*16,(asic+1)*16)))
    #ok_flag = (summary_output.check_quality("ADC_Gain", rows=range(asic*16,(asic+1)*16))).all()
    #ok_flag = (summary_output.check_quality("ADC_Gain_1_m", rows=range(asic*16,(asic+1)*16))).all()
    #ok_flag = ok_flag & (summary_output.check_quality("ADC_Gain_2_m", rows=range(asic*16,(asic+1)*16))).all()

    #if ok_flag:
    #plt.text(0.7, 0.3, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #plt.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["ADC_Gain_m"][0],summary_output.limits["ADC_Gain_m"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #else:
    #plt.text(0.7, 0.3, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #plt.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["ADC_Gain_m"][0],summary_output.limits["ADC_Gain_m"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #outstr = "bad channels: "+" ".join(bad_ch)
    #plt.text(0.7, 0.1, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    #adc_values = np.array(adc_values)
    #plt.legend(loc='best',ncol=2,fontsize='small')
    #plt.title("ADC linearity ASIC " + str(asic))
    #figname=outdir+"/adc_linearity_asic"+str(asic)+".png"
    #plt.savefig(figname)
    #plt.clf()

##############
    all_chlist=[]
    for asic in range(4):
        tmp_chlist = []
        for ch in range(16):
            if asic*16+ch in channel_list:
                tmp_chlist.append(asic*16+ch)
        all_chlist.append(tmp_chlist)

#########################################################################
    ## linearity plots
    plt.figure()
    ax = plt.subplot(111)
    for asic in range(4):
        plt.cla()
        tmp_chlist = all_chlist[asic]
        plot_linearity(ax,ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=tmp_chlist, title="ADC linearity ASIC " + str(asic), legend=True)
        figname=outdir+"/adc_linearity_asic"+str(asic)+".png"
        plt.savefig(figname)

    ax=plt.gca()
    plt.cla()
    plot_linearity(ax, ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=channel_list, title="ADC linearity (all channels)", legend=False)
    figname=outdir+"/adc_linearity_allchannels.png"
    plt.savefig(figname)
    ax.cla()





###########################################################################

## ADC precision
    ax.cla()

    for asic in range(4):
        plt.cla()
        tmp_chlist = all_chlist[asic]
#    for asic in range(nasics):
        plt.xlabel("Amplitude of input signal (p.e.)")
        plt.ylabel("ADC precision (%)")
        for chan in tmp_chlist:
            ch = chan%16
            color=my_col[ch]
#        for ch in range(16):
#            chan = ch + asic*16
#            if chan not in myout.ch:
#                #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
#                break
            y_value = []
            y_value_err = []
            x_value = []
            for x in ampl_list:
                amplitude = x
                #x_value.append(amplitude)
                #y_value.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Sigma"))
                #y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Sigma"))
                y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
                x_value.append(y_value[-1]/4) ## rough conversion to ADC/p.e.
                y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
                y_value[-1] = y_value_err[-1]/y_value[-1]
            y_value = np.array(y_value)
            #plt.errorbar(x = x_value, y = y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(ch + asic*16))
            plt.errorbar(x = x_value, y = y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(chan))

        #xxx,yyy = np.loadtxt("Cattura.txt",delimiter=",").T
        #plt.plot(xxx,yyy*100, color='r', linestyle='-', label='Requirement')
        #xxx,yyy = np.loadtxt("Cattura2.txt",delimiter=",").T
        #plt.plot(xxx,yyy*100, color='k', linestyle='-', label='Goal')
        if plt.gca().has_data():
            plt.legend(loc='best',ncol=3,fontsize='small')
        plt.title("ADC precision ASIC " + str(asic))
        plt.xscale('log')
        plt.yscale('log')
        figname=outdir+"/adc_precision1_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.clf()

        ####
        plt.xlabel("Amplitude of input signal (p.e.)")
        plt.ylabel("ADC precision (%)")
        for chan in tmp_chlist:
            ch = chan%16
            color=my_col[ch]
#        for ch in range(16):
#            chan = ch + asic*16
#            if chan not in myout.ch:
#                #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
#                break
            y_value = []
            y_value_err = []
            x_value = []
            for x in ampl_list:
                amplitude = x
                #y_value.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Sigma"))
                #y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Sigma"))
                y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
                x_value.append(y_value[-1]/4) ## rough conversion to ADC/p.e.
                y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
            #x_value = adc_values[ch]/4
            y_value = np.array(y_value)
            y_value_err = np.array(y_value_err)/(5000.**0.5)
            plt.errorbar(x = x_value, y = y_value_err/y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(chan))

        if plt.gca().has_data():
            plt.legend(loc='best',ncol=2,fontsize='small')
        plt.title("ADC precision ASIC " + str(asic))
        #plt.xscale('log')
        #plt.yscale('log')
        figname=outdir+"/adc_precision_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.clf()


    figname='linearity_gain_distribution'
    ax=plt.gca()
    plot_linearity_gain_distribution(ax, slopes)
    plt.savefig(outdir+figname+".png")


    figname='linearity_gain_vs_channel'
    #plot_linearity_gain_vs_channel(ax, myout.ch, slopes)
    plot_linearity_gain_vs_channel(ax, channel_list, slopes)
    plt.savefig(outdir+figname+".png")






    fig = plt.figure(figsize=(4*2,3*2))

    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(212)
    plot_linearity_gain_distribution(ax1, slopes)
    plot_linearity(ax2, ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=channel_list, title="ADC linearity (all channels)", legend=False)
    #plot_linearity_gain_vs_channel(ax3, myout.ch, slopes)
    plot_linearity_gain_vs_channel(ax3, channel_list, slopes)

    plt.tight_layout()
    plt.savefig(outdir+"linearity_summary.png")
    plt.clf()





    ## generate html
    for i,chan in enumerate(channel_list):
    #for asic in range(nasics):
        asic = int(chan/16)
        ch = chan%16
        #summary_file.write("{0}\t{1:.4e}\t{1:.4e}\t{1:.4e}\n".format(chan,slopes[chan],slopes1[chan],slopes2[chan]))
    #summary_file.close()
    summary_output.save_to_file(outdir+ "/summary_results_signal2.txt", sep=";")

    summary_output = MyOutput(data=pd.read_csv(outdir+ "/summary_results_signal2.txt", header=0, sep=";"))
    summary_output.add_limits_to_output(mode=output_results_mode)
    flag = summary_output.check_quality("ADC_Gain_m")
    #flag1 = summary_output.check_quality("ADC_Gain_1_m")
    #flag2 = summary_output.check_quality("ADC_Gain_2_m")
    summary_output.save_to_html(outdir+ "/summary_results_signal.html")
    summary_output.save_to_file(outdir+ "/summary_results_signal.txt", sep="\t", align_colnames=True)

    nbad_ch = np.logical_not(flag).sum()

    return nbad_ch

def do_dacs_plots(filenames,smart_dacs,outdir,chlist=None):
    key="max_ampl_mean_wf"
    colors=get_colors(max(len(smart_dacs),25))
    my_col = get_col_map(colors)
    plt.clf()
    figname=outdir+"/summary_"+key+".png"
    data=[]
    data_err=[]
    for filename,dac in zip(filenames,smart_dacs):
        filename_res = filename.replace("_r0.tio","")+"/results_signal2.txt"
        myout = MyOutput(data=pd.read_csv(filename_res, header=0, sep=";"))
        channel_list = []
        val_list = []
        val_err = []
        for ch in myout.ch:
            ch = int(ch)
            row = myout.loc[myout.ch==ch]
            channel_list.append(ch)
            val_list.append(row[key].values[0])
            val_err.append(row[key+"_err"].values[0])
            color=my_col[smart_dacs.index(dac)]
        data.append(val_list)
        data_err.append(val_err)
        plt.errorbar(channel_list, val_list,yerr=val_err,marker='o',label="dac {0}".format(dac),markersize=3.5,linestyle='None',color=color)
        plt.xlabel("Channel id")
        plt.ylabel(key.replace("_", " "))
        plt.legend(loc="best")
        plt.savefig(figname)

    data=np.asarray(data)
    data_err=np.asarray(data_err)
    nplotmax=16 #number of curves per plot
    nexc=(np.shape(data)[1])%nplotmax
    nplots=int((np.shape(data)[1])/nplotmax)
    slopes_all=[]
    nchans_for_plots=[np.arange(0,32,2),np.arange(1,32,2),np.arange(32,64,2),np.arange(33,64,2)]
       
    for i in range(nplots):
        slopes=[]
        plt.clf()
        plt.tight_layout()
        plt.title(key.replace("_"," ") + " summary")
        plt.xlabel("DAC")
        plt.ylabel(key.replace("_"," "))
        figname=outdir+"/summary_"+key+"_"+str(i)+".png"
        #for j in range(nplotmax):
            #index=i*nplotmax + j
        for j,index in enumerate(nchans_for_plots[i]):
            yvec=data[:,index].tolist()
            yerr=data_err[:,index].tolist()
            color=my_col[j]
            plt.errorbar(smart_dacs,yvec, yerr=yerr,marker='o', label="Ch " +str(index),markersize=3.5,color=color,linestyle='None',elinewidth=0.7)
            coeff, var_matrix = curve_fit(lin_funct, np.asarray(smart_dacs,dtype=np.float32), np.asarray(yvec,dtype=np.float32),sigma=np.asarray(yerr,dtype=np.float32),absolute_sigma = True)
            coeff, var_matrix = curve_fit(lin_funct, np.asarray(smart_dacs,dtype=np.float32), np.asarray(yvec,dtype=np.float32),sigma=np.asarray(yerr,dtype=np.float32),absolute_sigma = True,p0=coeff)
            slopes_all.append(coeff[1])
            slopes.append(coeff[1])
            fitline=[lin_funct(x, *coeff) for x in smart_dacs]
            plt.errorbar(smart_dacs,fitline,marker='None',linestyle='--',color=color,linewidth=0.7)
    
        plt.legend(loc="best",ncol=2)
        plt.savefig(figname)

        plt.clf()
        ax=plt.gca()
        figname="DAC_slopes_"+str(i)
        gauss_distribution(ax, slopes, bins=10, title="", xtitle="Slope of DAC curve", ytitle="Entries", dofit=True, figname=figname, outdir=outdir, message="", limits=None, ylog=False, optimize_range=True, xlimits=None, range_tuple=None)
        plt.savefig(outdir+figname+".png")
        
    plt.clf()
    ax=plt.gca()
    figname="DAC_slopes"
    gauss_distribution(ax, slopes_all, bins=10, title="", xtitle="Slope of DAC curve", ytitle="Entries", dofit=True, figname=figname, outdir=outdir, message="", limits=None, ylog=False, optimize_range=True, xlimits=None, range_tuple=None)
    
    plt.savefig(outdir+figname+".png")
    #gauss_distribution2(slopes, bins=30, title="", xtitle="Slope of DAC curve", ytitle="Entries", dofit=False, figname=figname, outdir=outdir, message="", ylog=False)

    logger.log(logger.TEST_LEVEL_MESS,"channels: {0}".format(len(myout.ch)))
        
    
    
def do_sipm_plots(filenames,smart_globals, outdir, chlist=None):
    keys=["mean_ampl_sipm", "fwhm_mean_ampl_sipm", "pulse_tau"]
    colors=get_colors(min(len(smart_globals),25))
    my_col = get_col_map(colors)
    nplotmax=3
    nexc=len(smart_globals)%nplotmax
    nplots=int(len(smart_globals)/nplotmax)
    summary_sg=[[16,5,40],[0,0,63],[0,32,32],[0,63,0]]
    summary_fn=[]
    for key in keys:
        for i in range(nplots):
            plt.clf()
            plt.tight_layout()
            plt.title(key.replace("_"," ") + " summary")
            plt.xlabel("Channel id")
            plt.ylabel(key.replace("_", " "))
            figname=outdir+"/summary_"+key+"_"+str(i)+".png"
            start=i*nplots
            if i==nplots-1:
                stop=(i+1)*nplots +nexc
            else:
                stop=(i+1)*nplots
            print (filenames)
            for filename, sg in zip(filenames[start:stop],smart_globals[start:stop]):
                filename_res = filename.replace("_r0.tio","")+"/results_signal2.txt"
                if sg in summary_sg:
                    summary_fn.append(filename_res)
                myout = MyOutput(data=pd.read_csv(filename_res, header=0, sep=";"))
                channel_list = []
                val_list = []
                val_err = []
                for ch in myout.ch:
                    ch = int(ch)
                    row = myout.loc[myout.ch==ch]
                    channel_list.append(ch)
                    val_list.append(row[key].values[0])
                    val_err.append(row[key+"_sigma"].values[0])
                    color=my_col[smart_globals.index(sg)]
                plt.errorbar(channel_list, val_list,yerr=val_err,marker='o',label="SMART_{0}_{1}_{2}".format(sg[0],sg[1],sg[2]),markersize=3.5,linestyle='None',color=color)
                plt.legend(loc="best")
                plt.savefig(figname)
                        
    logger.log(logger.TEST_LEVEL_MESS,"channels: {0}".format(len(myout.ch)))

    fig = plt.figure(figsize=(4*2,3*2))

    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(212)
    
        
    for fn, sg in zip(summary_fn,summary_sg):
        myout = MyOutput(data=pd.read_csv(fn, header=0, sep=";"))
        key="mean_ampl_sipm"
        channel_list = []
        val_list = []
        val_err = []
        for ch in myout.ch:
            ch = int(ch)
            row = myout.loc[myout.ch==ch]
            channel_list.append(ch)
            val_list.append(row[key].values[0])
            val_err.append(row[key+"_sigma"].values[0])
            color=my_col[smart_globals.index(sg)]
        ax1.errorbar(channel_list, val_list,yerr=val_err,marker='o',label="SMART_{0}_{1}_{2}".format(sg[0],sg[1],sg[2]),markersize=3.5,linestyle='None',color=color)
        ax1.set_title(key)
        ax1.set_xlabel("Channel id")
        ax1.set_ylabel(key)


        key="fwhm_mean_ampl_sipm"
        channel_list = []
        val_list = []
        val_err = []
        for ch in myout.ch:
            ch = int(ch)
            row = myout.loc[myout.ch==ch]
            channel_list.append(ch)
            val_list.append(row[key].values[0])
            val_err.append(row[key+"_sigma"].values[0])
            color=my_col[smart_globals.index(sg)]
        ax2.errorbar(channel_list, val_list,yerr=val_err,marker='o',label="SMART_{0}_{1}_{2}".format(sg[0],sg[1],sg[2]),markersize=3.5,linestyle='None',color=color)
        ax2.set_title(key)
        ax2.set_xlabel("Channel id")
        ax2.set_ylabel(key)

        key="pulse_tau"
        channel_list = []
        val_list = []
        val_err = []
        for ch in myout.ch:
            ch = int(ch)
            row = myout.loc[myout.ch==ch]
            channel_list.append(ch)
            val_list.append(row[key].values[0])
            val_err.append(row[key+"_sigma"].values[0])
            color=my_col[smart_globals.index(sg)]
        ax3.errorbar(channel_list, val_list,yerr=val_err,marker='o',label="SMART_{0}_{1}_{2}".format(sg[0],sg[1],sg[2]),markersize=3.5,linestyle='None',color=color)
        ax3.set_title(key)
        ax3.set_xlabel("Channel id")
        ax3.set_ylabel(key)
    
    ax1.legend(loc="best")
    ax2.legend(loc="best")
    ax3.legend(loc="best")
    plt.tight_layout()
    plt.savefig(outdir+"linearity_summary.png")
    plt.clf()    

    '''
    summary_filename = outdir+ "/summary_results_signal.txt"

    columns = ['Channel', 'ADC_Gain_m', 'ADC_Gain_q']
    types = ['int32','float32','float32']
    summary_output = MyOutput(columns=columns).set_types(types)

    ### Performing amplitude in ADC vs amplitude of input signal ###

    slopes=[]
    slopes1=[]
    slopes2=[]        
    
    if chlist is not None:
        channel_list = chlist

    for chan in channel_list:
        asic = int(chan/16)
        ch = chan%16
        bad_ch=[]

        if chan not in summary_output["Channel"].tolist():
            summary_output.loc[len(summary_output),"Channel"]=chan

        y_value = []
        y_value_err = []
        x_value = []
        x_value_fit1 = []
        y_value_fit1 = []
        y_value_fit1_err = []
        x_value_fit2 = []
        y_value_fit2 = []
        y_value_fit2_err = []
        for sg in smart_globals:
            x_value.append(amplitude)
            y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
            y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
            if y_value[-1]<=500:
                x_value_fit1.append(x_value[-1])
                y_value_fit1.append(y_value[-1])
                y_value_fit1_err.append(y_value_err[-1])
            else:
                x_value_fit2.append(x_value[-1])
                y_value_fit2.append(y_value[-1])
                y_value_fit2_err.append(y_value_err[-1])

        x_value = np.array(x_value)
        color=my_col[ch]
        x_value_fit1 = np.array(x_value_fit1)
        y_value_fit1 = np.array(y_value_fit1)
        y_value_fit1_err = np.array(y_value_fit1_err)

        x_value_fit2 = np.array(x_value_fit2)
        y_value_fit2 = np.array(y_value_fit2)
        y_value_fit2_err = np.array(y_value_fit2_err)

        a,b,r,p,e = stats.linregress(ampl_list,y_value)
        slopes.append(a)
        #a1,b1,r1,p1,e1 = stats.linregress(x_value_fit1,y_value_fit1)
        a1,b1 = a,b
        slopes1.append(a1)
        #a2,b2,r2,p2,e2 = stats.linregress(x_value_fit2,y_value_fit2)
        a2,b2=a,b
        slopes2.append(a2)

        ##plt.errorbar(x = x_value, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        #plt.errorbar(x = x_value, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(chan))
        ##plt.plot(x_value, a*x_value+b, linestyle='--', color=color)
        #plt.plot(x_value_fit1, a1*x_value_fit1+b1, linestyle='--', color=color)
        #plt.plot(x_value_fit2, a2*x_value_fit2+b2, linestyle='--', color=color)
        #adc_values.append(y_value)
        summary_output.loc[summary_output.Channel==chan, "ADC_Gain_m"] = a
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_1_m"] = a1
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_2_m"] = a2
        summary_output.loc[summary_output.Channel==chan, "ADC_Gain_q"] = b
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_1_q"] = b1
        #summary_output.loc[summary_output.Channel==chan, "ADC_Gain_2_q"] = b2

        #flag = summary_output.check_quality("ADC_Gain_m", rows=len(summary_output)-1)
        #flag1 = summary_output.check_quality("ADC_Gain_1_m", rows=len(summary_output)-1)
        #flag2 = summary_output.check_quality("ADC_Gain_2_m", rows=len(summary_output)-1)
        #logger.debug("Flag for ADC_Gain on channel "+str(chan)+" is: " +str(flag))
        #logger.debug("Flag for ADC_Gain from fit in two ranges on channel "+str(chan)+" is: " +str(flag1 & flag2))
        #if not flag:
        #    #if not flag1 & flag2:
        #    bad_ch.append(str(chan))
        ##logger.log(logger.TEST_LEVEL_MESS,"rows: {0}".format(range(asic*16,(asic+1)*16)))
    #ok_flag = (summary_output.check_quality("ADC_Gain", rows=range(asic*16,(asic+1)*16))).all()
    #ok_flag = (summary_output.check_quality("ADC_Gain_1_m", rows=range(asic*16,(asic+1)*16))).all()
    #ok_flag = ok_flag & (summary_output.check_quality("ADC_Gain_2_m", rows=range(asic*16,(asic+1)*16))).all()

    #if ok_flag:
    #plt.text(0.7, 0.3, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #plt.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["ADC_Gain_m"][0],summary_output.limits["ADC_Gain_m"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #else:
    #plt.text(0.7, 0.3, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #plt.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["ADC_Gain_m"][0],summary_output.limits["ADC_Gain_m"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #outstr = "bad channels: "+" ".join(bad_ch)
    #plt.text(0.7, 0.1, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    #adc_values = np.array(adc_values)
    #plt.legend(loc='best',ncol=2,fontsize='small')
    #plt.title("ADC linearity ASIC " + str(asic))
    #figname=outdir+"/adc_linearity_asic"+str(asic)+".png"
    #plt.savefig(figname)
    #plt.clf()

##############
    all_chlist=[]
    for asic in range(4):
        tmp_chlist = []
        for ch in range(16):
            if asic*16+ch in channel_list:
                tmp_chlist.append(asic*16+ch)
        all_chlist.append(tmp_chlist)

#########################################################################
    ## linearity plots
    plt.figure()
    ax = plt.subplot(111)
    for asic in range(4):
        plt.cla()
        tmp_chlist = all_chlist[asic]
        plot_linearity(ax,ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=tmp_chlist, title="ADC linearity ASIC " + str(asic), legend=True)
        figname=outdir+"/adc_linearity_asic"+str(asic)+".png"
        plt.savefig(figname)

    ax=plt.gca()
    plt.cla()
    plot_linearity(ax, ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=channel_list, title="ADC linearity (all channels)", legend=False)
    figname=outdir+"/adc_linearity_allchannels.png"
    plt.savefig(figname)
    ax.cla()


###########################################################################

## ADC precision
    ax.cla()

    for asic in range(4):
        plt.cla()
        tmp_chlist = all_chlist[asic]
#    for asic in range(nasics):
        plt.xlabel("Amplitude of input signal (p.e.)")
        plt.ylabel("ADC precision (%)")
        for chan in tmp_chlist:
            ch = chan%16
            color=my_col[ch]
#        for ch in range(16):
#            chan = ch + asic*16
#            if chan not in myout.ch:
#                #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
#                break
            y_value = []
            y_value_err = []
            x_value = []
            for x in ampl_list:
                amplitude = x
                #x_value.append(amplitude)
                #y_value.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Sigma"))
                #y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Sigma"))
                y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
                x_value.append(y_value[-1]/4) ## rough conversion to ADC/p.e.
                y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
                y_value[-1] = y_value_err[-1]/y_value[-1]
            y_value = np.array(y_value)
            #plt.errorbar(x = x_value, y = y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(ch + asic*16))
            plt.errorbar(x = x_value, y = y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(chan))

        #xxx,yyy = np.loadtxt("Cattura.txt",delimiter=",").T
        #plt.plot(xxx,yyy*100, color='r', linestyle='-', label='Requirement')
        #xxx,yyy = np.loadtxt("Cattura2.txt",delimiter=",").T
        #plt.plot(xxx,yyy*100, color='k', linestyle='-', label='Goal')
        if plt.gca().has_data():
            plt.legend(loc='best',ncol=3,fontsize='small')
        plt.title("ADC precision ASIC " + str(asic))
        plt.xscale('log')
        plt.yscale('log')
        figname=outdir+"/adc_precision1_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.clf()

        ####
        plt.xlabel("Amplitude of input signal (p.e.)")
        plt.ylabel("ADC precision (%)")
        for chan in tmp_chlist:
            ch = chan%16
            color=my_col[ch]
#        for ch in range(16):
#            chan = ch + asic*16
#            if chan not in myout.ch:
#                #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
#                break
            y_value = []
            y_value_err = []
            x_value = []
            for x in ampl_list:
                amplitude = x
                #y_value.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.1f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Amplitude_fixed_time").get("Sigma"))
                #y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Value"))
                #y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(ch+asic*16)).get("Max_amplitude").get("Sigma"))
                y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Value"))
                x_value.append(y_value[-1]/4) ## rough conversion to ADC/p.e.
                y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get("Max_amplitude").get("Sigma"))
            #x_value = adc_values[ch]/4
            y_value = np.array(y_value)
            y_value_err = np.array(y_value_err)/(5000.**0.5)
            plt.errorbar(x = x_value, y = y_value_err/y_value*100, marker = '.',color=color,linestyle='--',label='ch'+str(chan))

        if plt.gca().has_data():
            plt.legend(loc='best',ncol=2,fontsize='small')
        plt.title("ADC precision ASIC " + str(asic))
        #plt.xscale('log')
        #plt.yscale('log')
        figname=outdir+"/adc_precision_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.clf()

    figname='linearity_gain_distribution'
    ax=plt.gca()
    plot_linearity_gain_distribution(ax, slopes)
    plt.savefig(outdir+figname+".png")

    figname='linearity_gain_vs_channel'
    #plot_linearity_gain_vs_channel(ax, myout.ch, slopes)
    plot_linearity_gain_vs_channel(ax, channel_list, slopes)
    plt.savefig(outdir+figname+".png")

    fig = plt.figure(figsize=(4*2,3*2))

    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(212)
    plot_linearity_gain_distribution(ax1, slopes)
    plot_linearity(ax2, ampl_list, data_dict, "Max_amplitude", summary_output, "ADC_Gain", channel_list=channel_list, title="ADC linearity (all channels)", legend=False)
    #plot_linearity_gain_vs_channel(ax3, myout.ch, slopes)
    plot_linearity_gain_vs_channel(ax3, channel_list, slopes)

    plt.tight_layout()
    plt.savefig(outdir+"linearity_summary.png")
    plt.clf()

    ## generate html
    for i,chan in enumerate(channel_list):
    #for asic in range(nasics):
        asic = int(chan/16)
        ch = chan%16
        #summary_file.write("{0}\t{1:.4e}\t{1:.4e}\t{1:.4e}\n".format(chan,slopes[chan],slopes1[chan],slopes2[chan]))
    #summary_file.close()
    summary_output.save_to_file(outdir+ "/summary_results_signal2.txt", sep=";")

    summary_output = MyOutput(data=pd.read_csv(outdir+ "/summary_results_signal2.txt", header=0, sep=";"))
    summary_output.add_limits_to_output(mode=output_results_mode)
    flag = summary_output.check_quality("ADC_Gain_m")
    #flag1 = summary_output.check_quality("ADC_Gain_1_m")
    #flag2 = summary_output.check_quality("ADC_Gain_2_m")
    summary_output.save_to_html(outdir+ "/summary_results_signal.html")
    summary_output.save_to_file(outdir+ "/summary_results_signal.txt", sep="\t", align_colnames=True)

    nbad_ch = np.logical_not(flag).sum()
    '''
    nbad_ch = 0
    
    return nbad_ch


def plot_vpedscan(ax,vped_vals, data_dict, data_key, summary_output, summary_tag, channel_list=None, title=None, legend=True):
    colors=get_colors(24)
    my_col = get_col_map(colors)
    if channel_list is None:
        channel_list = range(64)

    x_value_fit = []
    for vped in vped_vals:
        if vped>=1200 and vped<=3500:
            x_value_fit.append(vped)
    x_value_fit = np.array(x_value_fit)

    bad_ch=[]
    ax.set_xlabel("Vped (DAC units)")
    ax.set_ylabel("Pedestal position (ADC units)")
    for chan in channel_list:
        asic = int(chan/16)
        ch = chan%16
        color=my_col[ch]

        y_value = []
        y_value_err = []
        for vped in vped_vals:
            y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get(data_key).get("Value"))
            y_value_err.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get(data_key).get("Sigma",0))

        #a = summary_output.loc[summary_output.Channel==chan, "Slope_"+summary_tag].to_numpy()[0]
        #b = summary_output.loc[summary_output.Channel==chan, "Intercept_"+summary_tag].to_numpy()[0]
        a = summary_output.loc[summary_output.Channel==chan, summary_tag+"_m"].to_numpy()[0]
        b = summary_output.loc[summary_output.Channel==chan, summary_tag+"_q"].to_numpy()[0]

        ax.errorbar(x = vped_vals, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        ax.plot(x_value_fit, a*x_value_fit+b, linestyle='--', color=color)

        _rows = summary_output.index[summary_output.Channel==chan].tolist()[0]
        #flag = summary_output.check_quality("Slope_"+summary_tag, rows=_rows )
        flag = summary_output.check_quality(summary_tag+"_m", rows=_rows )
        logger.debug("Flag for Slope of "+summary_tag+" on channel "+str(chan)+" is: " +str(flag)) #### debug output
        if not flag:
            bad_ch.append(str(chan))

    _rows = summary_output.index[summary_output.Channel.isin(channel_list)].tolist()
    #ok_flag = (summary_output.check_quality("Slope_"+summary_tag, rows=_rows ) ).all()
    ok_flag = (summary_output.check_quality(summary_tag+"_m", rows=_rows ) ).all()

    slope_text = "Slope limits: [{0:.2f},{1:.2f}]".format(
        summary_output.limits[summary_tag+"_m"][0],
        summary_output.limits[summary_tag+"_m"][1]
    )

    print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.7, y_coord=0.5,
                    slope_text=slope_text, slope_x_coord=0.7, slope_y_coord=0.4,
                    bad_ch=bad_ch, bad_ch_x_coord=0.7, bad_ch_y_coord=0.3)

    # if ok_flag: #sigma >=limits[0] and sigma<=limits[1]:
    #     ax.text(0.7, 0.5, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #     ax.text(0.7, 0.4,  , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    # else:
    #     ax.text(0.7, 0.5, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #     ax.text(0.7, 0.4, , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #     outstr = "bad channels: "+" ".join(bad_ch)
    #     ax.text(0.7, 0.3, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    if legend and ax.has_data():
        ax.legend(loc='best',ncol=2,fontsize='small')
    if title is not None:
        ax.set_title(title)



def plot_vpedscan_summary(slopes, ax1,ax2, channel_list=None,xlimits=None):

    if channel_list is None:
        channel_list = range(64)
    title = "Pedestal/VPED distribution"
    xtitle = "Pedestal/VPED (ADC/DAC)"
    ytitle = "Entries"
    #figname = "summary_pedestal_over_vped_distribution"
    #tmp_mean,tmp_sigma=gauss_distribution2(slopes,20,title,xtitle,ytitle,False,figname,outdir)
    #ax=plt.gca()
    #tmp_mean,tmp_sigma,_,_=gauss_distribution(ax1,slopes,20,title,xtitle,ytitle,False,figname,outdir, xlimits=xlimits)
    tmp_mean,tmp_sigma,_,_ = \
        gauss_distribution(
            ax=ax1,
            data=slopes,
            bins=20,
            title=title,
            xtitle=xtitle,
            ytitle=ytitle,
            dofit=False,
            xlimits=xlimits
        )
    #plt.savefig(outdir+figname+".png")
    #plt.cla()


    ax2.set_title("Pedestal/VPED vs channel")
    ax2.set_xlabel("Channel")
    ax2.set_ylabel("Pedestal/VPED (ADC/DAC)")
    ax2.errorbar(channel_list,slopes, marker='o',markersize=4,linestyle=None)
    if xlimits is not None:
        ax2.axhline(y=xlimits[0], color='r', linestyle='--', alpha=0.7)
        ax2.axhline(y=xlimits[1], color='r', linestyle='--', alpha=0.7)
    #figname = "summary_pedestal_over_vped_vs_channel"
    #plt.savefig(outdir+figname+".png")
    #plt.cla()

def plot_triggerscan_summary(results_file,
                             ax1,ax2,ax3,ax4,ax5,ax6,ax7,ax8,
                             ax9,ax10,ax11,ax12,ax13,ax14,ax15,ax16,
                             target_hz=None,
                             group_list=None, flags=None):

    if group_list is None:
        group_list = range(16)

    #print(results_file)
    limits_df = pd.read_csv(results_file,sep='\t',nrows=2)
    results_df = pd.read_csv(results_file,sep='\t',skiprows=[1,2])
    limits_df.rename(columns=lambda x: x.strip(), inplace=True)
    results_df.rename(columns=lambda x: x.strip(), inplace=True)

    #groups_series = results_df["#Group"].loc[group_list]
    groups_series = results_df["group"]#.loc[group_list]

    #---limits---#
    plateau_start_limits_series = limits_df["plateau_start"]
    plateau_width_limits_series = limits_df["plateau_width"]
    plateau_height_limits_series = limits_df["plateau_height"]
    plateau_height_std_limits_series = limits_df["plateau_height_std"]

    peak_pos_limits_series = limits_df["peak_pos"]
    peak_width_limits_series = limits_df["peak_width"]
    peak_height_limits_series = limits_df["peak_height"]
    peak_plateau_dist_limits_series = limits_df["peak_plateau_dist"]

    #---data series---#
    plateau_start_series = results_df["plateau_start"]
    plateau_width_series = results_df["plateau_width"]
    plateau_height_series = results_df["plateau_height"]
    plateau_height_std_series = results_df["plateau_height_std"]

    peak_pos_series = results_df["peak_pos"]
    peak_width_series = results_df["peak_width"]
    peak_height_series = results_df["peak_height"]
    peak_plateau_dist_series = results_df["peak_plateau_dist"]

    plateau_start_xtitle = "Plateau start"
    plateau_width_xtitle = "Plateau width"
    plateau_height_xtitle = "Plateau height"
    plateau_height_std_xtitle = "Plateau height std"

    peak_pos_xtitle = "Peak position"
    peak_height_xtitle = "Peak height"
    peak_width_xtitle = "Peak width"
    peak_plateau_dist_xtitle = "Peak-plateau distance"

    ytitle = "Entries"

    ############# ATTENZIONE : usando range tuple si eliminano automaticamente i canali fuori dai limiti!! andrebbe tolto...
    #plateau distributions and plots

    #plateau_start_mean,plateau_start_sigma,_,_=gauss_distribution(ax1,plateau_start_series,bins=50,
    #                                                              range_tuple=(plateau_start_limits_series[0],
    #                                                                           plateau_start_limits_series[1]),
    #                                                          title = plateau_start_xtitle+" distribution",
    #                                                          xtitle = plateau_start_xtitle,
    #                                                          ytitle = ytitle,
    #                                                          dofit = False,
    #                                                          xlimits = plateau_start_limits_series)
    #plateau_width_mean,plateau_width_sigma,_,_=gauss_distribution(ax2,plateau_width_series,bins=50,
    #                                                              range_tuple=(plateau_width_limits_series[0],
    #                                                                           plateau_width_limits_series[1]),
    #                                                              title = plateau_width_xtitle+" distribution",
    #                                                              xtitle = plateau_width_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = plateau_width_limits_series)
    #plateau_height_mean,plateau_height_sigma,_,_=gauss_distribution(ax3,plateau_height_series,bins=10,
    #                                                                range_tuple=(plateau_height_limits_series[0],
    #                                                                           plateau_height_limits_series[1]),
    #                                                              title = plateau_height_xtitle+" distribution",
    #                                                              xtitle = plateau_height_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = plateau_height_limits_series)
    #if(target_hz!=None):
    #    ax3.axvline(x=target_hz, color='magenta', linestyle='--', alpha=1)
    #plateau_height_std_mean,plateau_height_std_sigma,_,_=gauss_distribution(ax4,plateau_height_std_series,bins=10,
    #                                                                        range_tuple=(plateau_height_std_limits_series[0],
    #                                                                           plateau_height_std_limits_series[1]),
    #                                                              title = plateau_height_std_xtitle+" distribution",
    #                                                              xtitle = plateau_height_std_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = plateau_height_std_limits_series)

    ax1.set_title(plateau_start_xtitle+" distribution")
    ax1.set_xlabel(plateau_start_xtitle)
    ax1.set_ylabel(ytitle)
    ax1.axvline(x=plateau_start_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax1.axvline(x=plateau_start_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax1.hist(plateau_start_series, bins=50, density=False,
             range=(min(plateau_start_limits_series[0],plateau_start_series.min()),
                    max(plateau_start_limits_series[1],plateau_start_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax1, ok_flag=flags[0].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[0])[0].astype(str) )

    ax2.set_title(plateau_width_xtitle+" distribution")
    ax2.set_xlabel(plateau_width_xtitle)
    ax2.set_ylabel(ytitle)
    ax2.axvline(x=plateau_width_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax2.axvline(x=plateau_width_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax2.hist(plateau_width_series, bins=50, density=False,
             range=(min(plateau_width_limits_series[0],plateau_width_series.min()),
                    max(plateau_width_limits_series[1],plateau_width_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax2, ok_flag=flags[1].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[1])[0].astype(str) )

    ax3.set_title(plateau_height_xtitle+" distribution")
    ax3.set_xlabel(plateau_height_xtitle)
    ax3.set_ylabel(ytitle)
    ax3.axvline(x=plateau_height_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax3.axvline(x=plateau_height_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax3.hist(plateau_height_series, bins=50, density=False,
             range=(min(plateau_height_limits_series[0],plateau_height_series.min()),
                    max(plateau_height_limits_series[1],plateau_height_series.max())),
             alpha=0.75, facecolor='green')
    if(target_hz!=None):
        ax3.axvline(x=target_hz, color='magenta', linestyle='--', alpha=1)
    if flags is not None:
        print_pass_fail(ax=ax3, ok_flag=flags[2].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[2])[0].astype(str) )

    ax4.set_title(plateau_height_std_xtitle+" distribution")
    ax4.set_xlabel(plateau_height_std_xtitle)
    ax4.set_ylabel(ytitle)
    ax4.axvline(x=plateau_height_std_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax4.axvline(x=plateau_height_std_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax4.hist(plateau_height_std_series, bins=50, density=False,
             range=(min(plateau_height_std_limits_series[0],plateau_height_std_series.min()),
                    max(plateau_height_std_limits_series[1],plateau_height_std_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax4, ok_flag=flags[3].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[3])[0].astype(str) )

    ax5.set_title(plateau_start_xtitle+" vs group")
    ax5.set_xlabel("group")
    ax5.set_ylabel(plateau_start_xtitle)
    ax5.errorbar(groups_series,plateau_start_series, marker='o',markersize=4,linestyle=None)
    ax5.axhline(y=plateau_start_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax5.axhline(y=plateau_start_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax5, ok_flag=flags[0].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[0])[0].astype(str) )

    ax6.set_title(plateau_width_xtitle+" vs group")
    ax6.set_xlabel("group")
    ax6.set_ylabel(plateau_width_xtitle)
    ax6.errorbar(groups_series,plateau_width_series, marker='o',markersize=4,linestyle=None)
    ax6.axhline(y=plateau_width_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax6.axhline(y=plateau_width_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax6, ok_flag=flags[1].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[1])[0].astype(str) )

    ax7.set_title(plateau_height_xtitle+" vs group")
    ax7.set_xlabel("group")
    ax7.set_ylabel(plateau_height_xtitle)
    ax7.errorbar(groups_series,plateau_height_series, marker='o',markersize=4,linestyle=None)
    ax7.axhline(y=plateau_height_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax7.axhline(y=plateau_height_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if(target_hz!=None):
        ax7.axhline(y=target_hz, color='magenta', linestyle='--', alpha=1)
    if flags is not None:
        print_pass_fail(ax=ax7, ok_flag=flags[2].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[2])[0].astype(str) )

    ax8.set_title(plateau_height_std_xtitle+" vs group")
    ax8.set_xlabel("group")
    ax8.set_ylabel(plateau_height_std_xtitle)
    ax8.errorbar(groups_series,plateau_height_std_series, marker='o',markersize=4,linestyle=None)
    ax8.axhline(y=plateau_height_std_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax8.axhline(y=plateau_height_std_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax8, ok_flag=flags[3].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[3])[0].astype(str) )



    #peak distributions and plot
    #peak_pos_mean,peak_pos_sigma,_,_=gauss_distribution(ax9,peak_pos_series,bins=20,
    #                                                    range_tuple=(peak_pos_limits_series[0],
    #                                                                 peak_pos_limits_series[1]),
    #                                                          title = peak_pos_xtitle+" distribution",
    #                                                          xtitle = peak_pos_xtitle,
    #                                                          ytitle = ytitle,
    #                                                          dofit = False,
    #                                                          xlimits = peak_pos_limits_series)
    #peak_width_mean,peak_width_sigma,_,_=gauss_distribution(ax10,peak_width_series,bins = 20,
    #                                                        range_tuple=(peak_width_limits_series[0],
    #                                                                 peak_width_limits_series[1]),
    #                                                              title = peak_width_xtitle+" distribution",
    #                                                              xtitle = peak_width_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = peak_width_limits_series)
    #peak_height_mean,peak_height_sigma,_,_=gauss_distribution(ax11,peak_height_series,bins = 10,
    #                                                          range_tuple=(peak_height_limits_series[0],
    #                                                                 peak_height_limits_series[1]),
    #                                                              title = peak_height_xtitle+" distribution",
    #                                                              xtitle = peak_height_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = peak_height_limits_series)
    #peak_plateau_dist_mean,peak_plateau_dist_sigma,_,_=gauss_distribution(ax12,peak_plateau_dist_series,bins=10,
    #                                                                      range_tuple=(peak_plateau_dist_limits_series[0],
    #                                                                 peak_plateau_dist_limits_series[1]),
    #                                                              title = peak_plateau_dist_xtitle+" distribution",
    #                                                              xtitle = peak_plateau_dist_xtitle,
    #                                                              ytitle = ytitle,
    #                                                              dofit = False,
    #                                                              xlimits = peak_plateau_dist_limits_series)
    ax9.set_title(peak_pos_xtitle+" distribution")
    ax9.set_xlabel(peak_pos_xtitle)
    ax9.set_ylabel(ytitle)
    ax9.axvline(x=peak_pos_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax9.axvline(x=peak_pos_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax9.hist(peak_pos_series, bins=50, density=False,
             range=(min(peak_pos_limits_series[0],peak_pos_series.min()),
                    max(peak_pos_limits_series[1],peak_pos_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax9, ok_flag=flags[4].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[4])[0].astype(str) )

    ax10.set_title(peak_width_xtitle+" distribution")
    ax10.set_xlabel(peak_width_xtitle)
    ax10.set_ylabel(ytitle)
    ax10.axvline(x=peak_width_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax10.axvline(x=peak_width_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax10.hist(peak_width_series, bins=50, density=False,
             range=(min(peak_width_limits_series[0],peak_width_series.min()),
                    max(peak_width_limits_series[1],peak_width_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax10, ok_flag=flags[5].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[5])[0].astype(str) )

    ax11.set_title(peak_height_xtitle+" distribution")
    ax11.set_xlabel(peak_height_xtitle)
    ax11.set_ylabel(ytitle)
    ax11.axvline(x=peak_height_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax11.axvline(x=peak_height_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax11.hist(peak_height_series, bins=50, density=False,
             range=(min(peak_height_limits_series[0],peak_height_series.min()),
                    max(peak_height_limits_series[1],peak_height_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax11, ok_flag=flags[6].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[6])[0].astype(str) )

    ax12.set_title(peak_plateau_dist_xtitle+" distribution")
    ax12.set_xlabel(peak_plateau_dist_xtitle)
    ax12.set_ylabel(ytitle)
    ax12.axvline(x=peak_plateau_dist_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax12.axvline(x=peak_plateau_dist_limits_series[1], color='r', linestyle='--', alpha=0.7)
    ax12.hist(peak_plateau_dist_series, bins=50, density=False,
             range=(min(peak_plateau_dist_limits_series[0],peak_plateau_dist_series.min()),
                    max(peak_plateau_dist_limits_series[1],peak_plateau_dist_series.max())),
             alpha=0.75, facecolor='green')
    if flags is not None:
        print_pass_fail(ax=ax12, ok_flag=flags[7].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[7])[0].astype(str) )

    ax13.set_title(peak_pos_xtitle+" vs group")
    ax13.set_xlabel("group")
    ax13.set_ylabel(peak_pos_xtitle)
    ax13.errorbar(groups_series,peak_pos_series, marker='o',markersize=4,linestyle=None)
    ax13.axhline(y=peak_pos_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax13.axhline(y=peak_pos_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax13, ok_flag=flags[4].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[4])[0].astype(str) )

    ax14.set_title(peak_width_xtitle+" vs group")
    ax14.set_xlabel("group")
    ax14.set_ylabel(peak_width_xtitle)
    ax14.errorbar(groups_series,peak_width_series, marker='o',markersize=4,linestyle=None)
    ax14.axhline(y=peak_width_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax14.axhline(y=peak_width_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax14, ok_flag=flags[5].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[5])[0].astype(str) )

    ax15.set_title(peak_height_xtitle+" vs group")
    ax15.set_xlabel("group")
    ax15.set_ylabel(peak_height_xtitle)
    ax15.errorbar(groups_series,peak_height_series, marker='o',markersize=4,linestyle=None)
    ax15.axhline(y=peak_height_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax15.axhline(y=peak_height_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax15, ok_flag=flags[6].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[6])[0].astype(str) )

    ax16.set_title(peak_plateau_dist_xtitle+" vs group")
    ax16.set_xlabel("group")
    ax16.set_ylabel(peak_plateau_dist_xtitle)
    ax16.errorbar(groups_series,peak_plateau_dist_series, marker='o',markersize=4,linestyle=None)
    ax16.axhline(y=peak_plateau_dist_limits_series[0], color='r', linestyle='--', alpha=0.7)
    ax16.axhline(y=peak_plateau_dist_limits_series[1], color='r', linestyle='--', alpha=0.7)
    if flags is not None:
        print_pass_fail(ax=ax16, ok_flag=flags[7].all(), x_coord=0.5, y_coord=0.85, bad_ch=np.where(~flags[7])[0].astype(str) )


def do_pedestal_plots(filenames,vped_vals, outdir, chlist=None):
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)

    data_dict={}
    '''
    for filename, vped in zip(filenames,vped_vals):
        #filename="plots/pedestal_exttrigger_nblocks4_packets4_vped"+str(vped)+"_delay500_r0/results_pedestal.txt"
        #filename=filename_ped%(vped)
        data_file = open(filename,"r")
        x = data_file.read()
        lines = x.split('\n')
        data_dict["vped"+str(vped)]={}
        for ch in range(0,len(lines)-2):
            data_dict["vped"+str(vped)]["Channel"+str(ch)]={}
            line = lines[ch+1].split('\t')
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped_average_cells_0-30"]={"Value":float(line[1]),"Sigma":float(line[2])}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped_average_cell_31"]={"Value":float(line[3]),"Sigma":float(line[4])}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped0_from_fit"]={"Value":float(line[7])}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Noise"]={"Value":float(line[5])}

        data_file.close()
    '''
    for filename, vped in zip(filenames,vped_vals):
        #filename="plots/pedestal_exttrigger_nblocks4_packets4_vped"+str(vped)+"_delay500_r0/results_pedestal.txt"
        #filename=filename_ped%(vped)
        filename_res = filename.replace("_r0.tio","")+"/results_pedestal2.txt"

        myout = MyOutput(data=pd.read_csv(filename_res, header=0, sep=";"))
        ## columns = ['Channel', 'Ped_avg_0_30', 'Ped_sigma_0_30', 'Ped_avg_31', 'Ped_sigma_31', 'Sigma_noise', 'Outliers', 'Ped0']
        data_dict["vped"+str(vped)]={}
        channel_list = []
        for ch in myout.ch:
            ch = int(ch)
            channel_list.append(ch)
            row = myout.loc[myout.ch==ch]
            data_dict["vped"+str(vped)]["Channel"+str(ch)]={}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped_average_cells_0-30"]={"Value": row["Ped_avg_0_30"].values[0] ,"Sigma": row["Ped_sigma_0_30"].values[0]}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped_average_cell_31"]={"Value": row["Ped_avg_31"].values[0] ,"Sigma": row["Ped_sigma_31"].values[0]}
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Ped0_from_fit"]={"Value": row["Ped0"].values[0] }
            data_dict["vped"+str(vped)]["Channel"+str(ch)]["Noise"]={"Value":row["Sigma_noise"].values[0]}



    summary_filename = outdir+ "/summary_results_pedestal.txt"
    #summary_file = open(summary_filename,"w")
    #summary_file.write('Channel\tSlope_Pedestal\tSlope_Pedestal_from_fit\n')

    #columns = ['Channel', 'Slope_Pedestal','Slope_Pedestal_from_fit']
    #columns = ['Channel', 'Slope_pedestal','Intercept_pedestal','Slope_pedestal_from_fit','Intercept_pedestal_from_fit']
    columns = ['Channel', 'Pedestal_m', 'Pedestal_q','Pedestal_fit_m','Pedestal_fit_q']

    types = ['int32','float32','float32','float32','float32']
    summary_output = MyOutput(columns=columns).set_types(types)

    ### Performing pedestal value vs vped plots ###
    slopes = []
    #plt.figure()
    #ax = plt.subplot(111)
    colors=get_colors(24)
    my_col = get_col_map(colors)

    #nasics = len(myout.ch) // 16
    #if (len(myout.ch)%16 != 0):
    #    nasics+=1

    #logger.log(logger.TEST_LEVEL_MESS,"nasics: {0}".format(nasics))

    if chlist is not None:
        channel_list = chlist

    for chan in channel_list:
    #for asic in range(nasics):
        asic = int(chan/16)
        ch = chan%16
        bad_ch=[]
        #plt.xlabel("Vped (DAC units)")
        #plt.ylabel("Pedestal position (ADC units)")
        #for ch in range(16):
        #    chan = ch + asic*16
        #    if chan not in myout.ch:
        #        #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
        #        break
        if chan not in summary_output["Channel"].tolist():
            summary_output.loc[len(summary_output),"Channel"]=chan
        x_value_fit = []
        y_value_fit = []
        y_value_fit_err = []
        y_value = []
        y_value_err = []
        for vped in vped_vals:
            #y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get("Ped_average_cells_0-30").get("Value"))
            #y_value_err.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get("Ped_average_cells_0-30").get("Sigma"))
            y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Ped_average_cells_0-30").get("Value"))
            y_value_err.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Ped_average_cells_0-30").get("Sigma"))
            if vped>=1200 and vped<=3500:
                x_value_fit.append(vped)
                y_value_fit.append(y_value[-1])
                y_value_fit_err.append(y_value_err[-1])
        x_value_fit = np.array(x_value_fit)
        #color=my_col[ch]
        a,b,r,p,e = stats.linregress(x_value_fit,y_value_fit)
        slopes.append(a)
        #plt.errorbar(x = vped_vals, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        #plt.plot(x_value_fit, a*x_value_fit+b, linestyle='--', color=color)
        #summary_output.loc[summary_output.Channel==chan, "Slope_pedestal"] = a
        #summary_output.loc[summary_output.Channel==chan, "Intercept_pedestal"] = b
        summary_output.loc[summary_output.Channel==chan, "Pedestal_m"] = a
        summary_output.loc[summary_output.Channel==chan, "Pedestal_q"] = b



        #flag = summary_output.check_quality("Slope_pedestal", rows=len(summary_output)-1)
        #logger.debug("Flag for Slope_pedestal on channel "+str(chan)+" is: " +str(flag)) #### debug output
        #if not flag:
        #    bad_ch.append(str(chan))
    #ok_flag = (summary_output.check_quality("Slope_pedestal", rows=range(asic*16,(asic+1)*16))).all()

    #if ok_flag: #sigma >=limits[0] and sigma<=limits[1]:
    #    plt.text(0.7, 0.5, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    plt.text(0.7, 0.4, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["Slope_pedestal"][0],summary_output.limits["Slope_pedestal"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #else:
    #    plt.text(0.7, 0.5, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    plt.text(0.7, 0.4, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["Slope_pedestal"][0],summary_output.limits["Slope_pedestal"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    outstr = "bad channels: "+" ".join(bad_ch)
    #    plt.text(0.7, 0.3, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    #plt.legend(loc='best',ncol=2,fontsize='small')
    #plt.title("Pedestal linearity ASIC " + str(asic))
    #figname=outdir+"/pedestal_linearity_asic"+str(asic)+".png"
    #plt.savefig(figname)
    #plt.clf()

    all_chlist=[]
    for asic in range(4):
        tmp_chlist = []
        for ch in range(16):
            if asic*16+ch in channel_list:
                tmp_chlist.append(asic*16+ch)
        all_chlist.append(tmp_chlist)

    plt.figure()
    ax = plt.subplot(111)
    for asic in range(4):
        tmp_chlist = all_chlist[asic]
        plot_vpedscan(ax,vped_vals, data_dict, "Ped_average_cells_0-30", summary_output, "Pedestal", channel_list=tmp_chlist, title="Pedestal linearity ASIC " + str(asic))
        figname=outdir+"/pedestal_linearity_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.cla()

    plot_vpedscan(ax,vped_vals, data_dict, "Ped_average_cells_0-30", summary_output, "Pedestal", channel_list=channel_list, legend=False, title="Pedestal linearity all ASICs")
    figname=outdir+"/pedestal_linearity_all_channels.png"
    plt.savefig(figname)
    plt.cla()

    #####################

    fig1,ax1 = plt.subplots(1)
    fig2,ax2 = plt.subplots(1)
    #my_xlimits = d['Slope_pedestal']
    my_xlimits = d['Pedestal_m']
    plot_vpedscan_summary(slopes, ax1,ax2, channel_list=channel_list,xlimits=my_xlimits)

    figname = "summary_pedestal_over_vped_distribution"
    fig1.savefig(outdir+figname+".png")
    ax1.cla()

    figname = "summary_pedestal_over_vped_vs_channel"
    fig2.savefig(outdir+figname+".png")
    ax2.cla()


    slopes1 = []
    for chan in channel_list:
    #for asic in range(nasics):
        asic = int(chan/16)
        ch = chan%16
        bad_ch=[]
        #plt.xlabel("Vped (DAC units)")
        #plt.ylabel("Pedestal position (ADC units)")
        #for ch in range(16):
        #    chan = ch + asic*16
        #    if chan not in myout.ch:
        #        #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
        #        break
        if chan not in summary_output["Channel"].tolist():
            summary_output.loc[len(summary_output),"Channel"]=chan
        x_value_fit = []
        y_value_fit = []
        y_value_fit_err = []
        y_value = []
        y_value_err = []
        for vped in vped_vals:
            #y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get("Ped0_from_fit").get("Value"))
            y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Ped0_from_fit").get("Value"))
            if vped>=1200 and vped<=3500:
                x_value_fit.append(vped)
                y_value_fit.append(y_value[-1])
                #y_value_fit_err.append(y_value_err[-1])
        #color=my_col[ch]
        ## implement double fit here if necessary or reduce fit range
        a,b,r,p,e = stats.linregress(x_value_fit, y_value_fit)#vped_vals,y_value)
        slopes1.append(a)
        #plt.errorbar(x = vped_vals, y = y_value, yerr = None, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        #plt.errorbar(x = vped_vals, y = y_value, yerr = None, marker = '.',linestyle='',color=color,label='ch'+str(chan))

        #plt.plot(vped_vals, a*vped_vals+b, linestyle='--', color=color)
        #summary_output.loc[summary_output.Channel==chan, "Slope_pedestal_from_fit"] = a
        #summary_output.loc[summary_output.Channel==chan, "Intercept_pedestal_from_fit"] = b
        summary_output.loc[summary_output.Channel==chan, "Pedestal_fit_m"] = a
        summary_output.loc[summary_output.Channel==chan, "Pedestal_fit_q"] = b


        #flag = summary_output.check_quality("Slope_pedestal_from_fit", rows=len(summary_output)-1)
        #logger.debug("Flag for Slope_pedestal_from_fit on channel "+str(chan)+" is: " +str(flag))
        #if not flag:
        #    bad_ch.append(str(chan))
    #ok_flag = (summary_output.check_quality("Slope_pedestal_from_fit", rows=range(asic*16,(asic+1)*16))).all()

    #if ok_flag: #sigma >=limits[0] and sigma<=limits[1]:
    #    plt.text(0.7, 0.5, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    plt.text(0.7, 0.4, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["Slope_pedestal_from_fit"][0],summary_output.limits["Slope_pedestal_from_fit"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #else:
    #    plt.text(0.7, 0.5, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    plt.text(0.7, 0.4, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits["Slope_pedestal_from_fit"][0],summary_output.limits["Slope_pedestal_from_fit"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #    outstr = "bad channels: "+" ".join(bad_ch)
    #    plt.text(0.7, 0.3, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    #plt.legend(loc='best',ncol=2,fontsize='small')
    #plt.title("Pedestal (from fit) linearity ASIC " + str(asic))
    #figname=outdir+"/pedestal_from_fit_linearity_asic"+str(asic)+".png"
    #plt.savefig(figname)
    #plt.clf()

    plt.figure()
    ax = plt.subplot(111)
    for asic in range(4):
        tmp_chlist = all_chlist[asic]
        plot_vpedscan(ax,vped_vals, data_dict,"Ped0_from_fit", summary_output,"Pedestal_fit", channel_list=tmp_chlist, title="Pedestal (from fit) linearity ASIC " + str(asic))
        figname=outdir+"/pedestal_fit_linearity_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.cla()

    plot_vpedscan(ax,vped_vals, data_dict,"Ped0_from_fit", summary_output,"Pedestal_fit", channel_list=channel_list, legend=False, title="Pedestal (from fit) linearity all ASICs")
    figname=outdir+"/pedestal_fit_linearity_all_channels.png"
    plt.savefig(figname)
    plt.cla()


    fig1,ax1 = plt.subplots(1)
    fig2,ax2 = plt.subplots(1)
    #my_xlimits = d['Slope_pedestal_from_fit']
    my_xlimits = d['Pedestal_fit_m']
    plot_vpedscan_summary(slopes1, ax1,ax2, channel_list=channel_list,xlimits=my_xlimits)
    figname = "summary_pedestal_fit_over_vped_distribution"
    fig1.savefig(outdir+figname+".png")
    ax1.cla()

    figname = "summary_pedestal_fit_over_vped_vs_channel"
    fig2.savefig(outdir+figname+".png")
    ax2.cla()


    fig = plt.figure(figsize=(4*2,3*2))
    ax1 = plt.subplot(221)
    ax2 = plt.subplot(222)
    ax3 = plt.subplot(212)
    plot_vpedscan(ax2,vped_vals, data_dict,"Ped0_from_fit", summary_output,"Pedestal_fit", channel_list=channel_list, legend=False, title="Pedestal (from fit) linearity all ASICs")
    plot_vpedscan_summary(slopes1, ax1,ax3, channel_list=channel_list,xlimits=my_xlimits)
    figname = "vpedscan_summary"
    fig.tight_layout()
    fig.savefig(outdir+figname+".png")

    ## noise vs vped
    fig = plt.figure()
    for asic in range(4):
        tmp_chlist = all_chlist[asic]
        plt.xlabel("Vped (DAC units)")
        plt.ylabel("Noise (ADC units)")
        for chan in tmp_chlist:
            ch = chan%16
            #chan = ch + asic*16
            #if chan not in myout.ch:
            #    #logger.log(logger.TEST_LEVEL_MESS,"{0} not there!!!".format(chan))
            #    break
            y_value = []
            y_value_err = []
            for vped in vped_vals:
                #y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(ch+asic*16)).get("Noise").get("Value"))
                y_value.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Noise").get("Value"))
            color=my_col[ch]
            #plt.errorbar(x = vped_vals, y = y_value, yerr = None, marker = '.',color=color,linestyle='--',label='ch'+str(ch + asic*16))
            plt.errorbar(x = vped_vals, y = y_value, yerr = None, marker = '.',color=color,linestyle='--',label='ch'+str(chan))

        if plt.gca().has_data():
            plt.legend(loc='best',ncol=2,fontsize='small')
        plt.title("Noise ASIC " + str(asic))
        figname=outdir+"/noise_vs_vped_asic"+str(asic)+".png"
        plt.savefig(figname)
        plt.clf()
    ###



    ## generate html
    #for i,chan in enumerate(channel_list):
    #for asic in range(nasics):
    #    asic = int(chan/16)
    #    ch = chan%16
        #summary_file.write("{0}\t{1:.4e}\t{2:.4e}\n".format(asic*16+ch,slopes[asic*16+ch], slopes1[asic*16+ch]))
    #    summary_file.write("{0}\t{1:.4e}\t{2:.4e}\n".format(chan,slopes[i], slopes1[i]))
    #summary_file.close()
    summary_output.save_to_file(outdir+ "/summary_results_pedestal2.txt", sep=";")

    summary_output = MyOutput(data=pd.read_csv(outdir+ "/summary_results_pedestal2.txt", header=0, sep=";"))
    summary_output.add_limits_to_output(mode=output_results_mode)
    #flag1 = summary_output.check_quality("Slope_pedestal")
    #flag2 = summary_output.check_quality("Slope_pedestal_from_fit")
    flag1 = summary_output.check_quality("Pedestal_m")
    flag2 = summary_output.check_quality("Pedestal_fit_m")
    summary_output.save_to_html(outdir+ "/summary_results_pedestal.html")
    summary_output.save_to_file(outdir+ "/summary_results_pedestal.txt", sep="\t", align_colnames=True)

    nbad_ch = np.logical_not(flag1*flag2).sum()


    ## pedestal comparison with the two methods -- just for debugging
    y1 = []
    y2 = []
    chan = channel_list[0]
    asic = int(chan/16)
    ch = chan%16
    for vped in vped_vals:
        y1.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Ped0_from_fit").get("Value"))
        y2.append(data_dict.get("vped"+str(vped)).get("Channel"+str(chan)).get("Ped_average_cells_0-30").get("Value"))

    plt.xlabel("Vped (DAC units)")
    plt.ylabel("Pedestal position (ADC units)")
    plt.errorbar(x = vped_vals, y = y1, yerr = None, marker = '.',color=my_col[0],linestyle='--',label='ped from fit')
    plt.errorbar(x = vped_vals, y = y2, yerr = None, marker = '.',color=my_col[1],linestyle='--',label='average ped')
    plt.legend(loc='best',ncol=2,fontsize='small')
    plt.title("Pedestal (from fit and average) linearity ASIC " + str(asic) + " channel " + str(ch))
    figname=outdir+"/pedestal_comparison_asic"+str(asic)+"channel"+str(ch)+".png"
    plt.savefig(figname)
    plt.clf()

    # return 0
    return nbad_ch

"""
def do_2d_plots(fname, asic):
    d = yaml.load(open(fname), Loader=yaml.FullLoader)[asic]
    m = np.zeros((16,16))
    for i in range(16):
        for j in range(16):
            k = str(i)+"_"+str(j)
            dd=d[k]
            logger.debug( "dd[3] = " + str(dd[3]))
            m[i,j] = dd[3]
    plt.figure()
    plt.imshow(m, origin='lower')
    plt.title("ASIC " + str(asic))
    cbar=plt.colorbar()
    cbar.set_label('dt (ns)')
    figname="plots/summary/adc_jitter_asic"+str(asic)+".png"
    plt.savefig(figname)
    return 0
"""

if __name__=="__main__":
    outdir = "./plots/"

    filename="data/pedestal_exttrigger_nblocks4_packets8_vped1200_delay500_r0.tio"
    fileped = filename.replace("_r0.tio","_ped.tcal")
    outdir += filename.replace(".tio","/")
    outdir = outdir.replace("data/","")
    os.system("mkdir -p " + outdir)
    filename_r1 = filename.replace("_r0.","_r1.")
    analyse_pedestal(fname_r0=filename, fname_r1=filename_r1, fname_ped=fileped, outdir=outdir, ch0=0, nch=1, tag="")

    outdir = "./plots/"
    filename_r0 = "data/signal_exttrigger_nblocks4_packets4_vped1200_delay430_r0.tio"
    filename_r1 = filename_r0.replace("_r0.tio","_r1.tio")
    outdir += filename_r1.replace("_r1.tio","/")
    outdir = outdir.replace("data/","")
    #outdir+="signal/"
    os.system("mkdir -p " + outdir)
    analyse_signal(fname_r1=filename_r1, fname_r0=filename_r0, outdir=outdir, ch0=0, nch=64, tag="")

def plot_noise_summary(ax, ch_id, all_sigma):
    ax.cla()
    title = "Noise summary"
    xtitle = "Noise (ADC counts)"
    ytitle = "Entries"
    figname = "8_summary_sigma_distribution"
    #mean_f,sigma_f=gauss_distribution2(all_sigma,20,title,xtitle,ytitle,False,figname,outdir)
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    my_xlimits = d['Sigma_noise']
    #logger.debug("my xlimits ------>" + str(my_xlimits))
    mean_f,sigma_f,_,_= \
        gauss_distribution(
            ax=ax,
            data=all_sigma,
            bins=20,
            title=title,
            xtitle=xtitle,
            ytitle=ytitle,
            dofit=True,
            xlimits=my_xlimits
        )


def plot_sigma_summary(ax, ch_id, all_sigma, print_text=False, ok_flag=False):
    ax.cla()
    ax.set_title("Noise")
    ax.set_xlabel("Channel id")
    ax.set_ylabel("Noise (ADC counts)")
    #ax.set_xlim(0,64)
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.errorbar(ch_id,all_sigma, marker='o',markersize=4,linestyle=None)
    ax.axhline(y=d['Sigma_noise'][0], color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=d['Sigma_noise'][1], color='r', linestyle='--', alpha=0.7)
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.15, y_coord=0.85)



def plot_outliers_summary(ax, ch_id, nspikes_tot, totalcells, print_text=False,
                          ok_flag=False):
    fname="limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.cla()
    ax.set_title("Outliers")
    ax.set_xlabel("Channel id")
    ax.set_ylabel("Entries")
    #ax.set_xlim(0,64)
    #ax.plot([0,63],[0.01*totalcells,0.01*totalcells],marker='',linestyle='--',color='r')
    #ax.plot([0,63],[0,0],marker='',linestyle='--',color='r')
    ax.errorbar(ch_id,nspikes_tot, marker='o',markersize=4,linestyle=None)
    ax.axhline(y=d['Outliers'][0], color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=d['Outliers'][1], color='r', linestyle='--', alpha=0.7)
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.15, y_coord=0.85)


def plot_max_ampl_distribution(ax, ch_id, mean_max_ampl_vals, print_text=False,
                               ok_flag=False):
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.set_title("max_ampl(mean) distribution")
    ax.set_xlabel("max_ampl(mean)")
    #ax.set_xlim(0,64)
    ax.set_ylabel("Entries")
    ax.axvline(x=d['max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    ax.axvline(x=d['max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    ax.hist(mean_max_ampl_vals, bins=20, density=False, range=None,
            alpha=0.75, facecolor='green')
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.5, y_coord=0.85)


def plot_max_ampl_summary(ax, ch_id, mean_max_ampl_vals, print_text=False,
                          ok_flag=False):
    fname="limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.set_title("max_ampl")
    ax.set_xlabel("Channel id")
    #ax.set_xlim(0,64)
    ax.set_ylabel("max_ampl(mean)")
    ax.errorbar(ch_id,mean_max_ampl_vals, marker='o',markersize=4,linestyle=None)
    ax.axhline(y=d['max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=d['max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.5, y_coord=0.85)


def plot_sigma_max_ampl_distribution(ax, ch_id, sigma_max_ampl_vals,
                                     print_text=False, ok_flag=False):
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.set_title("sigma_max_ampl distribution")
    ax.set_xlabel("sigma_max_ampl")
    #ax.set_xlim(0,64)
    ax.set_ylabel("Entries")
    ax.axvline(x=d['sigma_max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    ax.axvline(x=d['sigma_max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    ax.hist(sigma_max_ampl_vals, bins=20, density=False, range=None,
            alpha=0.75, facecolor='green')
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.5, y_coord=0.85)


def plot_sigma_max_ampl_summary(ax, ch_id, sigma_max_ampl_vals,
                                print_text=False, ok_flag=False):
    fname = "limits.yaml"
    d = {}
    with open(fname) as fptr:
        d = yaml.load(fptr, Loader=yaml.FullLoader)
    ax.set_title("sigma_max_ampl")
    ax.set_xlabel("Channel id")
    #ax.set_xlim(0,64)
    ax.set_ylabel("sigma_max_ampl")
    ax.errorbar(ch_id, sigma_max_ampl_vals, marker='o',
                markersize=4, linestyle=None)
    ax.axhline(y=d['sigma_max_ampl'][0], color='r', linestyle='--', alpha=0.7)
    ax.axhline(y=d['sigma_max_ampl'][1], color='r', linestyle='--', alpha=0.7)
    if print_text:
        print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.5, y_coord=0.85)



def plot_linearity(ax, ampl_list, data_dict, data_key, summary_output, summary_tag, channel_list=None, title=None, legend=True):
    colors=get_colors(24)
    my_col = get_col_map(colors)
    if channel_list is None:
        channel_list = range(64)


    bad_ch=[]
    ax.set_xlabel("Ampl. of input signal (Volts@Func.Gen)")
    ax.set_ylabel("Amplitude of digital signal (ADC units)")
    for chan in channel_list:
        asic = int(chan/16)
        ch = chan%16
        color=my_col[ch]

        y_value = []
        y_value_err = []
        x_value = []
        x_value_fit1 = []
        y_value_fit1 = []
        y_value_fit1_err = []
        x_value_fit2 = []
        y_value_fit2 = []
        y_value_fit2_err = []


        for x in ampl_list:
            amplitude = x
            x_value.append(amplitude)
            y_value.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get(data_key).get("Value"))
            y_value_err.append(data_dict.get("Signal_amplitude{0:.4f}".format(amplitude)).get("Channel"+str(chan)).get(data_key).get("Sigma"))
            if y_value[-1]<=500:
                x_value_fit1.append(x_value[-1])
                y_value_fit1.append(y_value[-1])
                y_value_fit1_err.append(y_value_err[-1])
            else:
                x_value_fit2.append(x_value[-1])
                y_value_fit2.append(y_value[-1])
                y_value_fit2_err.append(y_value_err[-1])

        x_value = np.array(x_value)
        x_value_fit1 = np.array(x_value_fit1)
        y_value_fit1 = np.array(y_value_fit1)
        y_value_fit1_err = np.array(y_value_fit1_err)

        x_value_fit2 = np.array(x_value_fit2)
        y_value_fit2 = np.array(y_value_fit2)
        y_value_fit2_err = np.array(y_value_fit2_err)


        a = summary_output.loc[summary_output.Channel==chan, summary_tag+"_m"].to_numpy()[0]
        b = summary_output.loc[summary_output.Channel==chan, summary_tag+"_q"].to_numpy()[0]
        #a1 = summary_output.loc[summary_output.Channel==chan, summary_tag+"_1_m"].to_numpy()[0]
        #b1 = summary_output.loc[summary_output.Channel==chan, summary_tag+"_1_q"].to_numpy()[0]
        #a2 = summary_output.loc[summary_output.Channel==chan, summary_tag+"_2_m"].to_numpy()[0]
        #b2 = summary_output.loc[summary_output.Channel==chan, summary_tag+"_2_q"].to_numpy()[0]

        ########
        ax.errorbar(x = x_value, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        ax.plot(x_value, a*x_value+b, linestyle='--', color=color)
        #ax.plot(x_value_fit1, a1*x_value_fit1+b1, linestyle='--', color=color)
        #ax.plot(x_value_fit2, a2*x_value_fit2+b2, linestyle='--', color=color)

        #ax.errorbar(x = vped_vals, y = y_value, yerr = y_value_err, marker = '.',linestyle='',color=color,label='ch'+str(ch + asic*16))
        #ax.plot(x_value_fit, a*x_value_fit+b, linestyle='--', color=color)

        _rows = summary_output.index[summary_output.Channel==chan].tolist()
        if len(_rows) > 1: raise Exception('Malformed output database, found two rows with the same channel id')
        if len(_rows) == 0:
            logger.log(logger.TEST_LEVEL_ERROR, "Could not find quality data for channel id" + str(chan))
            continue
        _rows = _rows[0]
        flag = summary_output.check_quality(summary_tag+"_m", rows=_rows )
        logger.debug("Flag for "+summary_tag+"_m on channel "+str(chan)+" is: " +str(flag)) #### debug output
        if not flag:
            bad_ch.append(str(chan))

    _rows = summary_output.index[summary_output.Channel.isin(channel_list)].tolist()
    ok_flag = (summary_output.check_quality(summary_tag+"_m", rows=_rows ) ).all()

    slope_text = "Slope limits: [{0:.2f},{1:.2f}]".format(
        summary_output.limits[summary_tag+"_m"][0],
        summary_output.limits[summary_tag+"_m"][1]
    )
    print_pass_fail(ax=ax, ok_flag=ok_flag, x_coord=0.7, y_coord=0.3,
                    slope_text=slope_text, slope_x_coord=0.7, slope_y_coord=0.2,
                    bad_ch=bad_ch, bad_ch_x_coord=0.7, bad_ch_y_coord=0.1)

    # if ok_flag:
    #         ax.text(0.7, 0.3, "PASS", fontsize=18, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #         ax.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits[summary_tag+"_m"][0],summary_output.limits[summary_tag+"_m"][1]) , fontsize=12, color='g', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    # else:
    #         ax.text(0.7, 0.3, "FAIL", fontsize=18, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #         ax.text(0.7, 0.2, "Slope limits: [{0:.2f},{1:.2f}]".format(summary_output.limits[summary_tag+"_m"][0],summary_output.limits[summary_tag+"_m"][1]) , fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)
    #         outstr = "bad channels: "+" ".join(bad_ch)
    #         ax.text(0.7, 0.1, outstr, fontsize=12, color='r', horizontalalignment='center', verticalalignment='top',transform = ax.transAxes)

    if legend and ax.has_data():
        ax.legend(loc='best',ncol=2,fontsize='small')
    if title is not None:
        ax.set_title(title)



def plot_linearity_gain_distribution(ax, slopes):
    ax.cla()
    fname = "limits.yaml"
    d={}
    with open(fname) as fptr:
            d = yaml.load(fptr, Loader=yaml.FullLoader)
    adc_gain_limits = d['ADC_Gain_m']
    title = "ADC gain distribution"
    xtitle = "ADC gain (ADC units/V)"
    ytitle = "Entries"
    figname = "summary_adc_gain"
    #tmp_mean,tmp_sigma=gauss_distribution2(slopes,20,title,xtitle,ytitle,False,figname,outdir)
    tmp_mean, tmp_sigma, _, _ = \
        gauss_distribution(
            ax=ax,
            data=slopes,
            bins=20,
            title=title,
            xtitle=xtitle,
            ytitle=ytitle,
            dofit=False,
            xlimits=adc_gain_limits
        )



def plot_linearity_gain_vs_channel(ax, ch_id, slopes):
    ax.cla()
    fname = "limits.yaml"
    d={}
    with open(fname) as fptr:
            d = yaml.load(fptr, Loader=yaml.FullLoader)
    adc_gain_limits = d['ADC_Gain_m']
    ax.set_title("ADC gain vs channel")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Gain (ADC units/V)")
    ax.errorbar(ch_id,slopes, marker='o',markersize=4,linestyle=None)
    ax.axhline(adc_gain_limits[0], color='r', linestyle='--', alpha=0.7)
    ax.axhline(adc_gain_limits[1], color='r', linestyle='--', alpha=0.7)

#-------------------------------------------------------------------------------
#-----------------------------   PELTIER FUNCTIONS   -----------------------------
#-------------------------------------------------------------------------------

def analyse_peltier(out_dir, peltier_file, limits_file):
    """Analyse peltier results stored in .yaml file

    Args:
        out_dir (str): directory where .yaml file is saved
        peltier_file (str): name of the .yaml peltier file
        limits_file (str): name of the .yaml limits file

    Returns:
        bool: fail
    """
    # Load peltier.yaml
    pelt_res = yaml.safe_load(open(os.path.join(out_dir, peltier_file), "r"))
    # Load safety limits
    lim = yaml.safe_load(open(limits_file, "r"))

    firm_vers = pelt_res["Peltier_firm_version"]
    firm_year = pelt_res["Peltier_firm_year"]
    firm_month = pelt_res["Peltier_firm_month"]
    firm_day = pelt_res["Peltier_firm_day"]

    # Create results plots directory
    plot_dir = os.path.join(out_dir, "peltier_summary_plots")
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Since int(False)=0 and int(True)=1
    text = ["PASS", "FAIL"]
    text_color = ["g", "r"]

    ## plot thermistor temperatures
    f, ax = plt.subplots(1, 2, figsize=(15, 5))
    t1 = pelt_res["Peltier_temp1"]
    t2 = pelt_res["Peltier_temp2"]
    t3 = pelt_res["Peltier_temp3"]
    t4 = pelt_res["Peltier_temp4"]
    x = ["Temp1","Temp2","Temp3","Temp4"]
    y1 = np.array([t1,t2,t3,t4])
    ymin = lim["sensor_temperature"][0]
    ymax = lim["sensor_temperature"][1]
    fail1 = np.logical_or(y1<ymin,y1>ymax).any()

    ax_ = ax[0]
    ax_.plot(x, y1, "o--", color="tab:blue")
    ax_.set_ylabel("Temperature (°C)")
    # Plot limits
    ax_.axhline(ymin, color="tab:red", linestyle="--")
    ax_.axhline(ymax, color="tab:red", linestyle="--")
    # Set title
    ax_.set_title("Thermistor temperatures")

    ax_.text(0.25, 0.25,
            text[int(fail1)], fontsize=18,
            color=text_color[int(fail1)],
            horizontalalignment='center', verticalalignment='top',
            transform=ax_.transAxes)

    #plt.savefig(os.path.join(plot_dir, "Thermistors.png"),
    #            bbox_inches="tight", dpi=300)


    if fail1:
        logger.log(logger.TEST_LEVEL_FAIL, "Peltier uC analysis: FAILED thermistor temperature check.")
    else:
        logger.log(logger.TEST_LEVEL_INFO, "Peltier uC analysis: PASS thermistor temperature check.")

    ## plot peltier current
    #f, ax = plt.subplots(1, 1)#, figsize=(15, 10))
    c0 = pelt_res["Peltier_curr_off_before"]
    c1 = pelt_res["Peltier_curr_on"]
    c2 = pelt_res["Peltier_curr_off_after"]
    x = ["OFF_before","ON","OFF_after"]
    y2 = np.array([c0,c1,c2])
    cmin = lim["peltier_current"][0]
    cmax = lim["peltier_current"][1]
    cnull_limit = 10 ## must be zero
    fail2 = (c1<cmin)|(c1>cmax)|(c0>cnull_limit)|(c2>cnull_limit)

    ax_ = ax[1]
    ax_.plot(x, y2, "o", color="tab:blue")
    ax_.set_ylabel("Current (mA)")
    # Plot limits
    ax_.axhline(cmin, color="tab:red", linestyle="--")
    ax_.axhline(cmax, color="tab:red", linestyle="--")
    ax_.axhline(cnull_limit, color="tab:grey", linestyle="--")
    # Set title
    ax_.set_title("Peltier current")

    ax_.text(0.25, 0.25,
            text[int(fail2)], fontsize=18,
            color=text_color[int(fail2)],
            horizontalalignment='center', verticalalignment='top',
            transform=ax_.transAxes)

    plt.savefig(os.path.join(plot_dir, "Peltier.png"),
                bbox_inches="tight", dpi=300)

    if fail2:
        logger.log(logger.TEST_LEVEL_FAIL, "Peltier uC analysis: FAILED peltier current check.")
    else:
        logger.log(logger.TEST_LEVEL_INFO, "Peltier uC analysis: PASS peltier current check.")

    # Save file
    columns = ['Firm_vers','Firm_year','Firm_month','Firm_day','Temp1','Temp2','Temp3','Temp4','Curr_off_before','Curr_on','Curr_off_after']
    types = ['int', 'int', 'int', 'int', 'float', 'float', 'float', 'float', 'float', 'float', 'float']
    pelt_output = MyOutput(columns=columns).set_types(types)
    pelt_output.loc[len(pelt_output), columns] = [firm_vers, firm_year, firm_month, firm_day]+y1.tolist()+y2.tolist()
    #val_list = [pow_res_dig[name][dkey] for dkey in dkeys ]
    #pelt_output.loc[powdig_output.Test == name, columns] = [name] + val_list #list(pow_res_dig[name].values())

    pelt_output.save_to_file(os.path.join(plot_dir, "results_peltier2.txt"), sep=";")
    pelt_output = MyOutput(data=pd.read_csv(os.path.join(plot_dir, "results_peltier2.txt"), header=0, sep=";"))

    pelt_output._limits["Temp1"] = pelt_output._limits["sensor_temperature"]
    pelt_output._limits["Temp2"] = pelt_output._limits["sensor_temperature"]
    pelt_output._limits["Temp3"] = pelt_output._limits["sensor_temperature"]
    pelt_output._limits["Temp4"] = pelt_output._limits["sensor_temperature"]
    pelt_output._limits["Curr_off_before"] = [0,cnull_limit]
    pelt_output._limits["Curr_on"] = pelt_output._limits["peltier_current"]
    pelt_output._limits["Curr_off_after"] = [0,cnull_limit]

    pelt_output.add_limits_to_output(mode=output_results_mode)

    for colname in columns:
        pelt_output.check_quality(colname)


    pelt_output.save_to_html(os.path.join(plot_dir, "results_peltier.html"))
    pelt_output.save_to_file(os.path.join(plot_dir, "results_peltier.txt"),
                            sep="\t", align_colnames=True)


    fail = fail1 | fail2
    return fail



#-------------------------------------------------------------------------------
#-----------------------------   POWER FUNCTIONS   -----------------------------
#-------------------------------------------------------------------------------

def analyse_power(out_dir, voltages_file, limits_file):
    """Analyse power results stored in .yaml file

    Args:
        out_dir (str): directory where .yaml file is saved
        voltages_file (str): name of the .yaml voltages file
        limits_file (str): name of the .yaml limits file

    Returns:
        bool: fail
        dict: flags dictionary
    """
    # Load voltages.yaml
    pow_res = yaml.safe_load(open(os.path.join(out_dir, voltages_file), "r"))

    # Load safety limits
    lim = yaml.safe_load(open(limits_file, "r"))

    # Create results plots directory
    plot_dir = os.path.join(out_dir, "power_summary_plots")
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Flag dictionary
    dstatus = {'power': True}

    # Power dictionary
    dpower = {
        "3V3": {"fail": False, "fail_tests": []},
        "5V0": {"fail": False, "fail_tests": []},
        "HVOFF": {"fail": False, "fail_tests": []},
        "HVON": {"fail": False, "fail_tests": []},
    }

    # Since int(False)=0 and int(True)=1
    text = ["PASS", "FAIL"]
    text_color = ["g", "r"]
    data_all = []

    #f, ax = plt.subplots(2, 2, figsize=(15, 10))
    f, ax = plt.subplots(2, 3, figsize=(22, 10))

    # Loop on tests
    for t, test in enumerate(dpower.keys()):
        logger.log(logger.TEST_LEVEL_INFO, "Analysing %s results..." % (test))


        if(t<2):
            d_label = [
                "AUX_%sA_VOLTS" % (test),
                "AUX_%sB_VOLTS" % (test),
                "PRIMARY_%sA_VOLTS" % (test),
                "PRIMARY_%sB_VOLTS" % (test)
            ]
            xtick = [d_[:-6] for d_ in d_label]
        else:
            d_label = [
                'AUX_HV1_%s_VOLTS' % (test),
                'AUX_HV2_%s_VOLTS' % (test),
                'PRIMARY_HV1_%s_VOLTS' % (test),
                'PRIMARY_HV2_%s_VOLTS' % (test),
            ]
            xtick = [d_[:-(7+len(test))] for d_ in d_label]

        data = [pow_res[l_] for l_ in d_label]
        data_all.append(data)

        dpower[test]["fail"] = False
        for i, dV_ in enumerate(data):
            # Limit test
            if(dV_ < lim[test][0] or dV_ > lim[test][1]):
                dpower[test]["fail"] = True  # Test failed
                dpower[test]["fail_tests"].append(xtick[i])  # Save failed test
                dstatus['power'] = False

        # Plot measures
        ax_ = ax[int(t/2), t % 2]
        ax_.plot(xtick, data, "o--", color="tab:blue")
        # Plot limits
        ax_.axhline(lim[test][0], color="tab:grey", linestyle="--")
        ax_.axhline(lim[test][1], color="tab:grey", linestyle="--")
        # Set title
        ax_.set_title(test)

        ax_.text(0.25, 0.75,
                text[int(dpower[test]["fail"])], fontsize=18,
                color=text_color[int(dpower[test]["fail"])],
                horizontalalignment='center', verticalalignment='top',
                transform=ax_.transAxes)

        if dpower[test]["fail"]:
            logger.log(logger.TEST_LEVEL_FAIL, "%s analysis: FAILED (%s)" %
                    (test, ", ".join(dpower[test]["fail_tests"])))
        else:
            logger.log(logger.TEST_LEVEL_INFO, "%s analysis: PASS" % test)


    #plt.savefig(os.path.join(plot_dir, "PowerAnalysis.png"),
    #            bbox_inches="tight", dpi=300)

    # 3V3, 5V0, HV Table
    tests = ["AUX_A", "AUX_B", "PRIMARY_A", "PRIMARY_B"]
    dkeys =  list(dpower.keys())
    columns = ['Test'] + dkeys
    types = ['str', 'float', 'float', 'float', 'float']
    pow_output = MyOutput(columns=columns).set_types(types)

    for i,test in enumerate(tests):
        pow_output.loc[len(pow_output), "Test"] = test
        pow_output.loc[pow_output.Test == test, columns] = \
            [test] + \
            [data_all[0][i], data_all[1][i], data_all[2][i], data_all[3][i]]
        flag = [
            pow_output.check_quality(dkeys[0], rows=len(pow_output)-1),
            pow_output.check_quality(dkeys[1], rows=len(pow_output)-1),
            pow_output.check_quality(dkeys[2], rows=len(pow_output)-1),
            pow_output.check_quality(dkeys[3], rows=len(pow_output)-1)
        ]

    pow_output.save_to_file(os.path.join(plot_dir, "results_power2.txt"), sep=";")
    pow_output = MyOutput(data=pd.read_csv(os.path.join(plot_dir, "results_power2.txt"), header=0, sep=";"))
    pow_output.add_limits_to_output(mode=output_results_mode)

    flags = [
        pow_output.check_quality(dkeys[0]),
        pow_output.check_quality(dkeys[1]),
        pow_output.check_quality(dkeys[2]),
        pow_output.check_quality(dkeys[3])
    ]

    pow_output.save_to_html(os.path.join(plot_dir, "results_power.html"))
    pow_output.save_to_file(os.path.join(plot_dir, "results_power.txt"),
                            sep="\t", align_colnames=True)


    # ------------------------
    # --- TEMPERATURE TEST ---
    # ------------------------
    # Init dict
    dpower["TEMP"] = {"fail": False, "fail_tests": []}
    dstatus['temp'] = True

    # Create keys
    # Subkeys
    board_k = ["AUX", "PRIMARY"]


    temp_keys = ["TEMP"]
    columns = ["Test"] + temp_keys
    types = ['str', 'float']
    temp_output = MyOutput(columns=columns).set_types(types)

    for board_k_ in board_k:
        # Build name
        name = "_".join([temp_keys[0], board_k_])
        temp_output.loc[len(temp_output), "Test"] = name

        # Build val list
        val_list = [pow_res[name]]
        temp_output.loc[temp_output.Test == name, columns] = \
            [name] + val_list

        # Check
        r_ = len(temp_output)-1
        flag = [
            temp_output.check_quality(temp_keys[0], rows=r_)
        ]

        if(not all(flag)):
            dpower["TEMP"]["fail"] = True
            dpower["TEMP"]["fail_tests"].append(name)
            dstatus['temp'] = False


    # Plot temperatures
    test = temp_keys[0]
    ax_ = ax[0,2]
    ax_.plot(board_k, temp_output[test], "o--", color="tab:blue")
    # Plot limits
    ax_.axhline(lim[test][0], color="tab:grey", linestyle="--")
    ax_.axhline(lim[test][1], color="tab:grey", linestyle="--")
    # Set title
    ax_.set_title(test)

    ax_.text(0.25, 0.75,
             text[int(dpower[test]["fail"])], fontsize=18,
             color=text_color[int(dpower[test]["fail"])],
             horizontalalignment='center', verticalalignment='top',
             transform=ax_.transAxes)

    # Save file
    temp_output.save_to_file(os.path.join(
        plot_dir, "results_temp2.txt"), sep=";")
    temp_output = MyOutput(data=pd.read_csv(os.path.join(
        plot_dir, "results_temp2.txt"), header=0, sep=";"))
    temp_output.add_limits_to_output(mode=output_results_mode)

    flags = [
        temp_output.check_quality(temp_keys[0])
    ]

    temp_output.save_to_html(os.path.join(plot_dir, "results_temp.html"))
    temp_output.save_to_file(os.path.join(plot_dir, "results_temp.txt"),
                            sep="\t", align_colnames=True)

    test = "TEMP"
    if dpower[test]["fail"]:
        logger.log(logger.TEST_LEVEL_FAIL, "%s analysis: FAILED (%s)" %
                   (test, ", ".join(dpower[test]["fail_tests"])))
    else:
        logger.log(logger.TEST_LEVEL_INFO, "%s analysis: PASS" % test)


    # ---------------
    # --- HV TEST ---
    # ---------------
    # Init dict
    dpower["HV"] = {"fail": False, "fail_tests": []}
    dstatus['hv'] = True

    # Create keys
    # Subkeys
    subkeys = ["CURRENT_OFF",
               "CURRENT_ON",
               "VOLTAGE_OFF",
               "VOLTAGE_ON"
               ]
    # Build hv_keys
    hv_keys = [
        "HV_%s_AMPERES" % subkeys[0],
        "HV_%s_AMPERES" % subkeys[1],
        "HV_%s_VOLTS" % subkeys[2],
        "HV_%s_VOLTS" % subkeys[3]
    ]

    tests = ["HV"]
    columns = ["Test"] + hv_keys
    types = ['str', 'float', 'float', 'float', 'float']
    hv_output = MyOutput(columns=columns).set_types(types)

    # Build name
    name = tests[0]
    hv_output.loc[len(hv_output), "Test"] = name


    # Build val list
    val_list = [
        pow_res[hv_keys[0]],
        pow_res[hv_keys[1]],
        pow_res[hv_keys[2]],
        pow_res[hv_keys[3]]
    ]
    hv_output.loc[hv_output.Test == name, columns] = \
        [name] + val_list

    # Check
    r_ = len(hv_output)-1
    flag = [
        hv_output.check_quality(hv_keys[0], rows=r_),
        hv_output.check_quality(hv_keys[1], rows=r_),
        hv_output.check_quality(hv_keys[2], rows=r_),
        hv_output.check_quality(hv_keys[3], rows=r_)
    ]

    if(not all(flag)):
        dpower["HV"]["fail"] = True
        dpower["HV"]["fail_tests"].append(name)
        dstatus['hv'] = False


    # Plot HV volts/amperes
    test = "HV"
    ax_ = ax[1,2]
    # Plot OFF
    test1 = "OFF"
    xtest = "HV_CURRENT_"+test1+"_AMPERES"
    ytest = "HV_VOLTAGE_"+test1+"_VOLTS"
    ax_.plot(hv_output[xtest], hv_output[ytest], "o--", color="tab:blue")
    # Plot limits
    #ax_.axhline(lim[ytest][0], color="tab:blue", linestyle="--")
    #ax_.axhline(lim[ytest][1], color="tab:blue", linestyle="--")
    #ax_.axvline(lim[xtest][0], color="tab:blue", linestyle="--")
    #ax_.axvline(lim[xtest][1], color="tab:blue", linestyle="--")
    rect = patches.Rectangle((lim[xtest][0],lim[ytest][0]),lim[xtest][1]-lim[xtest][0],lim[ytest][1]-lim[ytest][0],
                             linewidth=1,linestyle='--',edgecolor='tab:blue',facecolor='none')
    ax_.add_patch(rect)
    ax_.set_xlim(min(-0.005,hv_output[xtest].min()*0.9),
                 max(.05, hv_output[xtest].max()*1.1))
    ax_.set_ylim(min(30.,hv_output[ytest].min()*0.9),
                 max(40.,hv_output[ytest].min()*1.1))
    ax_.set_xlabel("CURRENT OFF (A)", color="tab:blue")
    ax_.set_ylabel("VOLTAGE OFF (V)", color="tab:blue")
    ax_.tick_params(axis='x', colors="tab:blue")
    ax_.tick_params(axis='y', colors="tab:blue")

    # Plot ON
    ax2_ = f.add_subplot(236, label="on",frame_on=False)
    test1 = "ON"
    xtest = "HV_CURRENT_"+test1+"_AMPERES"
    ytest = "HV_VOLTAGE_"+test1+"_VOLTS"
    ax2_.plot(hv_output[xtest], hv_output[ytest], "o--", color="tab:orange")
    # Plot limits
    #ax2_.axhline(lim[ytest][0], color="tab:orange", linestyle="--")
    #ax2_.axhline(lim[ytest][1], color="tab:orange", linestyle="--")
    #ax2_.axvline(lim[xtest][0], color="tab:orange", linestyle="--")
    #ax2_.axvline(lim[xtest][1], color="tab:orange", linestyle="--")
    rect = patches.Rectangle((lim[xtest][0],lim[ytest][0]),lim[xtest][1]-lim[xtest][0],lim[ytest][1]-lim[ytest][0],
                             linewidth=1,linestyle='--',edgecolor='tab:orange',facecolor='none')
    ax2_.add_patch(rect)
    # Set limits and break axis
    ax2_.set_xlim(min(-1.0,hv_output[xtest].min()*0.9),
                 max(1.0, hv_output[xtest].max()*1.1))
    ax2_.set_ylim(min(24.,hv_output[ytest].min()*0.9),
                 max(34.,hv_output[ytest].min()*1.1))
    ax2_.xaxis.tick_top()
    ax2_.yaxis.tick_right()

    ax2_.xaxis.set_label_position("top")
    ax2_.yaxis.set_label_position("right")


    # Set title
    #ax_.set_title(test)

    ax2_.set_xlabel("CURRENT ON (A)", color="tab:orange")
    ax2_.set_ylabel("VOLTAGE ON (V)", color="tab:orange")
    ax2_.tick_params(axis='x', colors="tab:orange")
    ax2_.tick_params(axis='y', colors="tab:orange")

    ax_.text(0.25, 0.75,
             text[int(dpower[test]["fail"])], fontsize=18,
             color=text_color[int(dpower[test]["fail"])],
             horizontalalignment='center', verticalalignment='top',
             transform=ax_.transAxes)


    # Save file
    hv_output.save_to_file(os.path.join(
        plot_dir, "results_hv2.txt"), sep=";")
    hv_output = MyOutput(data=pd.read_csv(os.path.join(
        plot_dir, "results_hv2.txt"), header=0, sep=";"))
    hv_output.add_limits_to_output(mode=output_results_mode)

    flags = [
        hv_output.check_quality(hv_keys[0]),
        hv_output.check_quality(hv_keys[1]),
        hv_output.check_quality(hv_keys[2]),
        hv_output.check_quality(hv_keys[3])
    ]

    hv_output.save_to_html(os.path.join(plot_dir, "results_hv.html"))
    hv_output.save_to_file(os.path.join(plot_dir, "results_hv.txt"),
                        sep="\t", align_colnames=True)

    test = "HV"
    if dpower[test]["fail"]:
        logger.log(logger.TEST_LEVEL_FAIL, "%s analysis: FAILED (%s)" %
                (test, ", ".join(dpower[test]["fail_tests"])))
    else:
        logger.log(logger.TEST_LEVEL_INFO, "%s analysis: PASS" % test)


    plt.savefig(os.path.join(plot_dir, "PowerAnalysis.png"),
                bbox_inches="tight", dpi=300)


    # ----------------
    # --- 0/1 TEST ---
    # ----------------
    dpower["DIGITAL"] = {"fail": False, "fail_tests": []}
    dstatus['power_dig'] = True

    dkeys = ['ZERO_BEFORE','ONE', 'ZERO_AFTER']

    # Find tests name
    pow_res_dig = {}

    for pow_res_key in pow_res.keys():
        for dkeys_ in dkeys:
            if dkeys_ in pow_res_key:
                pow_res_dig[pow_res_key[:-(len(dkeys_)+1)]] = {}

    # Fill tests
    for pow_res_key in pow_res.keys():
        for dkeys_ in dkeys:
            if dkeys_ in pow_res_key:
                pow_res_dig[pow_res_key[:-(len(dkeys_)+1)]][dkeys_] = \
                    pow_res[pow_res_key]

    columns = ['Test'] + dkeys
    types = ['str', 'int', 'int', 'int']
    powdig_output = MyOutput(columns=columns).set_types(types)

    # Fill tests by name
    for name in pow_res_dig.keys():
        #print(pow_res_dig[name])
        powdig_output.loc[len(powdig_output), "Test"] = name
        val_list = [pow_res_dig[name][dkey] for dkey in dkeys ]
        powdig_output.loc[powdig_output.Test == name, columns] = \
            [name] + val_list #list(pow_res_dig[name].values())
        # Check
        flag = [
            powdig_output.check_quality(dkeys[0], rows=len(powdig_output)-1),
            powdig_output.check_quality(dkeys[1], rows=len(powdig_output)-1),
            powdig_output.check_quality(dkeys[2], rows=len(powdig_output)-1)
        ]
        if(not all(flag)):
            dpower["DIGITAL"]["fail"] = True
            dpower["DIGITAL"]["fail_tests"].append(name)
            dstatus['power_dig'] = False


    # Save file
    powdig_output.save_to_file(os.path.join(plot_dir, "results_power_dig2.txt"), sep=";")
    powdig_output = MyOutput(data=pd.read_csv(os.path.join(plot_dir, "results_power_dig2.txt"), header=0, sep=";"))
#    powdig_output.add_limits_to_output(mode=output_results_mode)

    flags = [
        powdig_output.check_quality(dkeys[0]),
        powdig_output.check_quality(dkeys[1]),
        powdig_output.check_quality(dkeys[2])
    ]

    powdig_output.save_to_html(os.path.join(plot_dir, "results_power_dig.html"))
    powdig_output.save_to_file(os.path.join(plot_dir, "results_power_dig.txt"),
                            sep="\t", align_colnames=True)


    test = "DIGITAL"
    if dpower[test]["fail"]:
        logger.log(logger.TEST_LEVEL_FAIL, "%s analysis: FAILED (%s)" %
                    (test, ", ".join(dpower[test]["fail_tests"])))
    else:
        logger.log(logger.TEST_LEVEL_INFO, "%s analysis: PASS" % test)

    # ----------------
    # --- CLK TEST ---
    # ----------------
    # Init dict
    dpower["CLK"] = {"fail": False, "fail_tests": []}
    dstatus['clk'] = True

    # Create keys
    # Subkeys
    board_k = ["AUX", "PRIMARY"]
    div_k = ["DIV10", "DIV16"]
    sig_k = ["MISO_MUSIC",
             "MOSI_MUSIC",
             "RESET_MUSIC",
             "SCLK_MUSIC",
             "SMART_SPI_CLK",
             "SMART_SPI_RES",
             "SS_MUSIC0",
             "SS_MUSIC1",
             "SS_MUSIC2",
             "SS_MUSIC3"]

    clk_keys = ["N_DIV10", "MEAN_DIV10","N_DIV16", "MEAN_DIV16"]
    columns = ["Test"] + clk_keys
    types = ['str', 'int', 'float', 'int', 'float']
    clk_output = MyOutput(columns=columns).set_types(types)

    for board_k_ in board_k:
        for sig_k_ in sig_k:
            # Build name
            name = "_".join(["CLOCK", board_k_, sig_k_,
                             "CALIBRATED_NANOSECONDS"])
            clk_output.loc[len(clk_output), "Test"] = name

            # Build the two keys (for DIV10 and DIV16)
            div10_k = "_".join(["CLOCK", board_k_, "DIV10", sig_k_,
                                "CALIBRATED_NANOSECONDS"])
            div16_k = "_".join(["CLOCK", board_k_, "DIV16", sig_k_,
                                "CALIBRATED_NANOSECONDS"])

            # Build val list
            val_list = [pow_res[div10_k][0], pow_res[div10_k][3],
                        pow_res[div16_k][0], pow_res[div16_k][3]]
            clk_output.loc[clk_output.Test == name, columns] = \
                [name] + val_list

            # Check
            r_ = len(clk_output)-1
            flag = [
                clk_output.check_quality(clk_keys[0], rows=r_),
                clk_output.check_quality(clk_keys[1], rows=r_),
                clk_output.check_quality(clk_keys[2], rows=r_),
                clk_output.check_quality(clk_keys[3], rows=r_)
            ]

            if(not all(flag)):
                dpower["CLK"]["fail"] = True
                dpower["CLK"]["fail_tests"].append(name)
                dstatus['clk'] = False

    # Save file
    clk_output.save_to_file(os.path.join(
        plot_dir, "results_clk2.txt"), sep=";")
    clk_output = MyOutput(data=pd.read_csv(os.path.join(
        plot_dir, "results_clk2.txt"), header=0, sep=";"))
    clk_output.add_limits_to_output(mode=output_results_mode)

    flags = [
        clk_output.check_quality(clk_keys[0]),
        clk_output.check_quality(clk_keys[1]),
        clk_output.check_quality(clk_keys[2]),
        clk_output.check_quality(clk_keys[3])
    ]

    clk_output.save_to_html(os.path.join(plot_dir, "results_clk.html"))
    clk_output.save_to_file(os.path.join(plot_dir, "results_clk.txt"),
                            sep="\t", align_colnames=True)

    test = "CLK"
    if dpower[test]["fail"]:
        logger.log(logger.TEST_LEVEL_FAIL, "%s analysis: FAILED (%s)" %
                   (test, ", ".join(dpower[test]["fail_tests"])))
    else:
        logger.log(logger.TEST_LEVEL_INFO, "%s analysis: PASS" % test)

    fail = any([dpower[test]["fail"] for test in dpower.keys()])

    return fail, dstatus


def test_results_tag(lim, plot_dir, board, data, tag, xtick):
    """Test power board results

    Args:
        lim (dict): limits loaded from limits.yaml file
        plot_dir (str): output plots directory
        board (str): board to be tested
        data (list): data to be analysed
        tag (str): data tag
        xtick (list): plot x axis

    Returns:
        bool: test failed
        list: list of failed tests
    """
    # Test if values are in safety; if not, save the index of the failed test
    fail = False
    fail_tests = []
    for i,dV_ in enumerate(data):
        # Limit test
        if(dV_ < lim[tag][0] or dV_ > lim[tag][1]):
            fail = True # Test failed
            fail_tests.append(xtick[i]) # Save failed test

    # Since int(False)=0 and int(True)=1
    text = ["PASS", "FAIL"]
    text_color = ["g", "r"]

    # Fig
    fig, ax = plt.subplots()
    ax.set_xlabel("Tests")
    ax.set_ylabel("Power Voltages (V)")
    # Plot measures
    plt.plot(xtick, data, "o--", color="tab:blue")
    # Plot limits
    ax.axhline(lim[tag][0], color="tab:grey", linestyle="--")
    ax.axhline(lim[tag][1], color="tab:grey", linestyle="--")
    # Plot fail text
    ax.text(0.2, 0.7, text[int(fail)], fontsize=18,
            color=text_color[int(fail)],
            horizontalalignment='center', verticalalignment='top',
            transform=ax.transAxes)
    # Save figure
    plt.savefig(os.path.join(plot_dir, "%s_%s.png" % (board, tag)),
                dpi=300)
    return fail, fail_tests


def test_zero_logic_signals(pow_res, board):
    """Test logical signals

    Args:
        pow_res (dict): .yaml voltages file loaded using the yaml module
        board (str): board to be tested

    Returns:
        bool: test failed
        list: list of failed tests
    """
    fail, fail_tests = False, []

    for label in pow_res.keys():
        if (board in label):
            if ("_ZERO" in label):
                if(pow_res[label] != 0):
                    fail = True
                    fail_tests.append(label)
            elif ("_ONE" in label):
                if(pow_res[label] != 1):
                    fail = True
                    fail_tests.append(label)

    return fail, fail_tests


def print_pass_fail(ax, ok_flag, x_coord=0.15, y_coord=0.85, slope_text='',
                    slope_x_coord=0.7, slope_y_coord=0.4, bad_ch=[],
                    bad_ch_x_coord=0.7, bad_ch_y_coord=0.4):
    """Print PASS of FAIL text in Plots

    Args:
        ax (ax): plot axis
        ok_flag (ax): True to print "PASS", False to print "FAIL"
        x_coord (float, optional): "PASS" x coord. Defaults to 0.15.
        y_coord (float, optional): "PASS" y coord. Defaults to 0.85.
        slope_text (str, optional): Slope text. Defaults to ''.
        slope_x_coord (float, optional): Slope text x coord. Defaults to 0.7.
        slope_y_coord (float, optional): Slope text y coord. Defaults to 0.4.
        bad_ch (list, optional): Bad ch list. Defaults to [].
        bad_ch_x_coord (float, optional): Bad ch list x coord. Defaults to 0.7.
        bad_ch_y_coord (float, optional): Bad ch list y coord. Defaults to 0.4.
    """
    # PRINT PASS/FAIL
    if ok_flag:
        ax.text(x_coord, y_coord, "PASS", fontsize=18, color='g',
                horizontalalignment='center', verticalalignment='top',
                transform=ax.transAxes)
        slope_color = 'g'

    else:
        ax.text(x_coord, y_coord, "FAIL", fontsize=18, color='r',
                horizontalalignment='center', verticalalignment='top',
                transform=ax.transAxes)
        slope_color = 'r'

    # PRINT SLOPE TEXT
    if (slope_text != ''):
        ax.text(slope_x_coord, slope_y_coord, slope_text, fontsize=12,
                color=slope_color, horizontalalignment='center',
                verticalalignment='top', transform=ax.transAxes)

    # PRINT BAD CH
    if not ok_flag and len(bad_ch)>0:
        if (len(bad_ch)> 5):
            ch_str = "bad channels: %s ..." % (" ".join(bad_ch[:5]))
        else:
            ch_str = "bad channels: %s" % (" ".join(bad_ch))
        ax.text(bad_ch_x_coord, bad_ch_y_coord, ch_str, fontsize=12, color='r',
                horizontalalignment='center', verticalalignment='top',
                transform=ax.transAxes)




#-------------------------------------------------------------------------------
#-----------------------------   SMART FUNCTIONS   -----------------------------
#-------------------------------------------------------------------------------

def analyse_smart_calib(out_dir, infilename, limits_file=None):
    """Analyse smart calibration data stored in .txt file

    Args:
        out_dir (str): directory where .txt file is saved
        infilename (str): prefix of the name of the .txt files 
        limits_file (str): name of the .yaml limits file

    Returns:
        bool: fail
    """
    # Output dir for plots
    plot_dir = os.path.join(out_dir, "smart_summary_plots")
    outdir=plot_dir
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # Load data
    fname_calib = os.path.join(out_dir,infilename+"_calib.txt")
    fname_adc_mean = os.path.join(out_dir,infilename+"_adc_mean.txt")
    fname_adc_sigma = os.path.join(out_dir,infilename+"_adc_sigma.txt")

    adc_mean = np.loadtxt(fname_adc_mean)
    adc_sigma = np.loadtxt(fname_adc_sigma)
    calib_vals = np.loadtxt(fname_calib).astype(int)
    
    # Load safety limits
    if limits_file is not None:
        lim = yaml.safe_load(open(limits_file, "r"))
    else:
        lim = {}

    # Calibrate data
    adc_mean_calib = adc_mean.copy()
    adc_sigma_calib = adc_sigma.copy()
    for i in range(len(calib_vals)): # loop over channels
        adc_mean_calib[i,:calib_vals[i]] = adc_mean[i,-1]
        adc_mean_calib[i]=np.roll(adc_mean_calib[i],-calib_vals[i])
        adc_sigma_calib[i,:calib_vals[i]] = adc_sigma[i,-1]
        adc_sigma_calib[i]=np.roll(adc_sigma_calib[i],-calib_vals[i])

    columns = ['ch', 'Smart_Min_ADC', 'Smart_Max_ADC', 'Smart_Sigma_ADC_worse', 'Smart_ADC_slope', 'Smart_Calib']
    types = ['int32','float32','float32','float32','float32', 'int32']
    smart_output = MyOutput(columns=columns).set_types(types)
    
    nch = 16
    x_vec = np.arange(len(adc_mean[0]))

    ## Analysis
    # min, max value of adc_mean_calib
    # max value of adc_mean_sigma
    # slope
    min_adc = adc_mean_calib.min(axis=1)
    max_adc = adc_mean_calib.max(axis=1)
    max_adc_sigma = adc_sigma_calib.max(axis=1)
    slopes=[]
    for ch in range(len(calib_vals)): # loop over channels
        uplim = np.where(adc_mean_calib[ch]==max_adc[ch])[0][0]
        if uplim==0:
            uplim=1
        a,b,r,p,e = stats.linregress(x_vec[:uplim],adc_mean_calib[ch,:uplim])
        slopes.append(a)
        smart_output.loc[len(smart_output),"ch"]=ch
        smart_output.loc[smart_output.ch==ch, columns] = [ch,min_adc[ch],max_adc[ch],max_adc_sigma[ch],slopes[ch], calib_vals[ch]]
        ## check on last row
        flag1 = smart_output.check_quality("Smart_Min_ADC", rows=len(smart_output)-1)
        flag2 = smart_output.check_quality("Smart_Max_ADC", rows=len(smart_output)-1)
        flag3 = smart_output.check_quality("Smart_Sigma_ADC_worse", rows=len(smart_output)-1)
        flag4 = smart_output.check_quality("Smart_ADC_slope", rows=len(smart_output)-1)
        flag5 = smart_output.check_quality("Smart_Calib", rows=len(smart_output)-1)
        flag = flag1 & flag2 & flag3 & flag4 & flag5
        logger.debug("Flag for SMART calibration on channel "+str(ch)+" is: " +str(flag)) #### debug output
        
    smart_output.save_to_file(os.path.join(plot_dir, "results_smart_calib2.txt"), sep=";")
    smart_output = MyOutput(data=pd.read_csv(os.path.join(plot_dir, "results_smart_calib2.txt"), header=0, sep=";"))
    smart_output.add_limits_to_output(mode=output_results_mode)

    flag1 = smart_output.check_quality("Smart_Min_ADC")
    #rows=list(np.arange(1,len(ped_output)))) #first row after header is limits row: do not check!!!
    flag2 = smart_output.check_quality("Smart_Max_ADC")
    #rows=list(np.arange(1,len(ped_output)))) #first row after header is limits row: do not check!!!
    flag3 = smart_output.check_quality("Smart_Sigma_ADC_worse")
    flag4 = smart_output.check_quality("Smart_ADC_slope")
    flag5 = smart_output.check_quality("Smart_Calib")
    nbad_ch = np.logical_not(flag1*flag2*flag3*flag4*flag5).sum()

    smart_output.save_to_html(os.path.join(plot_dir, "results_smart_calib.html"))
    smart_output.save_to_file(os.path.join(plot_dir, "results_smart_calib.txt"),
                              sep="\t", align_colnames=True)



    ####### Plot
    ## Raw ADC
    f, ax = plt.subplots(2, 2, figsize=(16, 10))
    for t in range(4):
        ax_ = ax[int(t/2), t % 2]
        for j in range(t*nch,(t+1)*nch):
            ax_.errorbar(x_vec, adc_mean[j], yerr=adc_sigma[j], marker=".", ls="--", label=f'ch{j}')#, color="tab:blue")
        # Plot limits
        #ax_.axhline(lim[test][0], color="tab:grey", linestyle="--")
        #ax_.axhline(lim[test][1], color="tab:grey", linestyle="--")
        # Set title
        ax_.set_title(f"SMART {t} - raw")

        #ax_.text(0.25, 0.75,
        #        text[int(dpower[test]["fail"])], fontsize=18,
        #        color=text_color[int(dpower[test]["fail"])],
        #        horizontalalignment='center', verticalalignment='top',
        #        transform=ax_.transAxes)

        ax_.set_xlabel("DAC-17")
        ax_.set_ylabel("ADC")
        ax_.legend(loc='best',ncol=2)
    plt.savefig(os.path.join(plot_dir, "SmartCalib_raw.png"),
                bbox_inches="tight", dpi=300)

    ## Calib ADC
    f, ax = plt.subplots(2, 2, figsize=(16, 10))
    for t in range(4):
        ax_ = ax[int(t/2), t % 2]
        for j in range(t*nch,(t+1)*nch):
            ax_.errorbar(x_vec, adc_mean_calib[j], yerr=adc_sigma_calib[j], marker=".", ls="--", label=f'ch{j}')#, color="tab:blue")
        # Plot limits
        #ax_.axhline(lim[test][0], color="tab:grey", linestyle="--")
        #ax_.axhline(lim[test][1], color="tab:grey", linestyle="--")
        # Set title
        ax_.set_title(f"SMART {t} - calib")

        #ax_.text(0.25, 0.75,
        #        text[int(dpower[test]["fail"])], fontsize=18,
        #        color=text_color[int(dpower[test]["fail"])],
        #        horizontalalignment='center', verticalalignment='top',
        #        transform=ax_.transAxes)

        ax_.set_xlabel("DAC-17")
        ax_.set_ylabel("ADC")
        ax_.legend(loc='best',ncol=2)
    plt.savefig(os.path.join(plot_dir, "SmartCalib_calib.png"),
                bbox_inches="tight", dpi=300)

    ## Calib vals
    f, ax = plt.subplots()
    ax.plot(np.arange(len(calib_vals)), calib_vals)
    ax.set_xlabel("Channel")
    ax.set_ylabel("Calibration value (DAC-17 count)")
    ax.set_title("Calibration values")
    plt.savefig(os.path.join(plot_dir, "SmartCalib_cal_values.png"),
                bbox_inches="tight", dpi=300)
    
  

    return nbad_ch
