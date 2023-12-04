"""
Given a list of files, set the CAMERAVERSION keyword in the fits header
"""
import argparse
from argparse import ArgumentDefaultsHelpFormatter as Formatter
import glob
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning
import warnings
warnings.filterwarnings('ignore', category=AstropyWarning, append=True)
from IPython import embed


def get_cameraversion(fp):
    h = fits.getheader(fp, 0)
    if 'EVENT_HEADER_VERSION' not in h:
        raise IOError("File is not a tio fits file")
    cv = h.get('CAMERAVERSION', '')
    return cv


def write(f, cv):
    fits.setval(f, 'CAMERAVERSION', value=cv)


def main():
    description = 'Set the CAMERAVERSION keyword in the fits header'
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=Formatter)
    parser.add_argument('-v', '--version', dest='cameraversion',
                        action='store', required=True,
                        help='version to store')
    parser.add_argument('--overwrite', dest='overwrite',
                        action='store_true',
                        help='overwrite the keyword it it already exists')
    parser.add_argument('-f', '--files', dest='files', action='store',
                        nargs='*', help='files to operate on')
    parser.add_argument('-d', '--directory', dest='directory', action='store',
                        help='directory to loop through all files '
                             'recursively, overrules "files" argument')
    args = parser.parse_args()

    cv = args.cameraversion
    ow = args.overwrite
    if args.directory:
        list_of_files = glob.glob(args.directory + '/**/*', recursive=True)
    else:
        list_of_files = args.files

    for fp in list_of_files:
        try:
            existing_cv = get_cameraversion(fp)
            if existing_cv:
                if ow:
                    write(fp, cv)
                    print("Version overwrote: {}->{} - {}"
                          .format(existing_cv, cv, fp))
                else:
                    print("No change: {} - {}".format(existing_cv, fp))
            else:
                write(fp, cv)
                print("Version set: {} - {}".format(cv, fp))
        except IOError:
            print("File is not a tio fits file: {}".format(fp))


if __name__ == '__main__':
    main()
