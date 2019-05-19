#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Making pretty plots."""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.colorbar import Colorbar

plt.rc('text', usetex=True)
rcParams.update({'axes.linewidth': 1.5})
rcParams.update({'xtick.direction': 'in'})
rcParams.update({'ytick.direction': 'in'})
rcParams.update({'xtick.minor.visible': 'True'})
rcParams.update({'ytick.minor.visible': 'True'})
rcParams.update({'xtick.major.pad': '7.0'})
rcParams.update({'xtick.major.size': '8.0'})
rcParams.update({'xtick.major.width': '1.5'})
rcParams.update({'xtick.minor.pad': '7.0'})
rcParams.update({'xtick.minor.size': '4.0'})
rcParams.update({'xtick.minor.width': '1.5'})
rcParams.update({'ytick.major.pad': '7.0'})
rcParams.update({'ytick.major.size': '8.0'})
rcParams.update({'ytick.major.width': '1.5'})
rcParams.update({'ytick.minor.pad': '7.0'})
rcParams.update({'ytick.minor.size': '4.0'})
rcParams.update({'ytick.minor.width': '1.5'})
rcParams.update({'axes.titlepad': '10.0'})
rcParams.update({'font.size': 25})


__all__ = ['FILTERS_COLOR', 'plot_skyobj_hist', 'map_skyobjs']

FILTERS_COLOR = ['#2ca02c', '#ff7f0e', '#d62728', '#8c564b', '#7f7f7f']
FILTERS_SHORT = ['g', 'r', 'i', 'z', 'y']

def plot_skyobj_hist(X, summary, filt, prop, region=None, aper=None, fontsize=20):
    """Making 1-D summary plot of the sky objects."""
    # Range of the X-axis
    x_range = [summary['low'], summary['upp']]

    # Color for the filter
    color_use = FILTERS_COLOR[FILTERS_SHORT.index(filt)]

    # Start the figure
    fig = plt.figure(figsize=(6, 5))
    fig.subplots_adjust(left=0.01, right=0.995, bottom=0.186, top=0.996)
    ax1 = fig.add_subplot(111)

    # Grid
    ax1.grid(linestyle='--', alpha=0.3, linewidth=1.5, color='gray')

    # Vertical line to highlight 0
    ax1.axvline(
        0.0, linewidth=2.0, linestyle='-', c='gray', alpha=1.0, zorder=0)

    # Histogram
    _ = ax1.hist(X, bins='auto', density=True, histtype='stepfilled', alpha=0.4,
                 label=r'$\mathrm{Hist}$', range=x_range, color=color_use, zorder=1)

    # KDE curve
    if summary['kde'] is not None:
        x_grid = np.linspace(summary['low'], summary['upp'], 500)
        ax1.plot(x_grid, summary['kde'].evaluate(x_grid), linewidth=2.5, alpha=0.9,
                 label=r'$\mathrm{KDE}$', color=color_use, zorder=2)

    # highlight the mean and median
    ax1.axvline(summary['mean'], linewidth=2.5, linestyle='--', c=color_use,
                label=r'$\rm Mean$', zorder=3, alpha=0.9)
    ax1.axvline(summary['median'], linewidth=2.0, linestyle=':', c=color_use,
                label=r'$\rm Median$', zorder=4, alpha=0.9)

    ax1.legend(fontsize=18, loc='best')

    if prop == 'flux':
        ax1.set_xlabel(r'$\mathrm{Flux\ }[\mu\mathrm{Jy}]$', fontsize=30)
    elif prop == 'snr':
        ax1.set_xlabel(r'$\mathrm{S/N}$', fontsize=30)
    elif prop == 'mu':
        ax1.set_xlabel(r'$\mu\ [\mu\mathrm{Jy}/\mathrm{arcsec}^2]$', fontsize=30)
    else:
        raise Exception("# Wrong type of properties: flux/snr/mu")

    # Remove the Y-axis tick labels
    ax1.yaxis.set_ticklabels([])

    # Show some basic statistics
    if region is not None:
        _ = ax1.text(0.04, 0.92, region, fontsize=fontsize,
                     horizontalalignment='left', verticalalignment='center',
                     transform=ax1.transAxes)

    if aper is not None:
        _ = ax1.text(0.04, 0.83, aper, fontsize=fontsize,
                     horizontalalignment='left', verticalalignment='center',
                     transform=ax1.transAxes)

    _ = ax1.text(0.04, 0.74, r'$N:{0}$'.format(len(X)), fontsize=fontsize,
                 horizontalalignment='left', verticalalignment='center',
                 transform=ax1.transAxes)

    _ = ax1.text(0.04, 0.65, r'$\mu:{0:8.5f}$'.format(summary['mean']), fontsize=fontsize,
                 horizontalalignment='left', verticalalignment='center',
                 transform=ax1.transAxes, color='k')

    _ = ax1.text(0.04, 0.56, r'$\sigma:{0:8.5f}$'.format(summary['std']), fontsize=fontsize,
                 horizontalalignment='left', verticalalignment='center',
                 transform=ax1.transAxes, color='k')

    _ = ax1.text(0.04, 0.47, r'$\rm m:{0:8.5f}$'.format(summary['median']),
                 fontsize=fontsize, horizontalalignment='left', verticalalignment='center',
                 transform=ax1.transAxes, color='k')

    return fig

def map_skyobjs(x, y, n, mu, label=None, n_min=10, vmin=None, vmax=None, 
                y_size=4, margin=0.2, fontsize=30, cbar_label=False):
    """Map the RA, Dec distributions of sky objects."""
    # Only keey the bins with enough sky objects in them
    mu[n <= n_min] = np.nan

    xy_ratio = (x.max() - x.min()) / (y.max() - y.min())

    fig = plt.figure(figsize=(xy_ratio * y_size, y_size))
    ax1 = fig.add_subplot(111)

    ax1.grid(linestyle='--', alpha=0.6)
    im = ax1.imshow(mu.T, origin='lower', extent=[x[0], x[-1], y[0], y[-1]],
                    aspect='equal', interpolation='nearest', 
                    cmap=plt.get_cmap('coolwarm'), vmin=vmin, vmax=vmax)

    ax1.set_xlim(x.min() - margin, x.max() + margin)
    ax1.set_ylim(y.min() - margin, y.max() + margin)

    if label is not None:
        plt.text(0.03, 1.05, label, transform=ax1.transAxes, fontsize=38)

    # Color bar
    cb_axes = fig.add_axes([0.48, 0.90, 0.37, 0.06])
    cb = Colorbar(ax=cb_axes, mappable=im, orientation='horizontal', ticklocation='top')
    if cbar_label:
        cb.set_label(r'$\mu{\rm Jy}/\mathrm{arcsec}^2$', fontsize=25)

    _ = ax1.set_xlabel(r'$\mathrm{R.A.\ [deg]}$', fontsize=fontsize)
    _ = ax1.set_ylabel(r'$\mathrm{Dec\ [deg]}$', fontsize=fontsize)

    return fig