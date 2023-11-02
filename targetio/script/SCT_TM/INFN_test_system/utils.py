import os
import sys
import re
import numpy as np
import yaml
import pandas as pd
from pandas.io.formats.style import Styler
import logging
import argparse
from fpdf import FPDF
from PIL import Image
import subprocess


testing_mode = True

#class Globals(dict):
#    def __init__(self):
#        self["my_ip"] = "192.168.12.3"
#        self["module_ip"] = "192.168.12.173"
#        self["asic_def"] = "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def"
#        self["trigger_asic_def"] = "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def"
#        self["module_def"] = "/home/target5/SCT_MSA_FPGA_Firmware0xC0000004.def"

#global_connection_details = Globals()

global_connection_details = {
    "my_ip" : "192.168.12.3",
    "module_ip" : "192.168.12.173",
    "asic_def" : "/home/target5/Software/TargetDriver/trunk/config/TC_ASIC.def",
    "trigger_asic_def" : "/home/target5/Software/TargetDriver/trunk/config/T5TEA_ASIC.def",
    "module_def" : "/home/target5/SCT_MSA_FPGA_Firmware0xC0000004.def"
}

def update_global_connection_details(my_ip=None,module_ip=None,asic_def=None,trigger_asic_def=None,module_def=None):
    if my_ip is not None:
        global_connection_details["my_ip"]=my_ip
    if module_ip is not None:
        global_connection_details["module_ip"]=module_ip
    if asic_def is not None:
        global_connection_details["asic_def"]=asic_def
    if trigger_asic_def is not None:
        global_connection_details["trigger_asic_def"]=trigger_asic_def
    if module_def is not None:
        global_connection_details["module_def"]=module_def

#defaults = {
#        "nblocks": 8,
#        "packets":8,
#        "daq_time": 10.,
#        "triggerdelay": 500,
#        "triggertype": 1,
#        "vped": 1200,
#        "vpedstart": 100,
#        "vpedstop": 4000,
#        "vpedstep": 100,
#        "sigstart": 0,
#        "sigstop": 0.3,
#        "sigstep": 0.05,
#        "sigfreq": 1113,
#}

def get_info(svn=True,cmd=True):
    svn_ver = os.popen("svnversion").read().strip() if svn else ""
    cmd = " ".join(sys.argv) if cmd else ""
    return svn_ver,cmd


def init_parser(key=None, sipm=False):
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument("-m" ,"--module", help="Module ID", type=int, default=0)
    base_parser.add_argument("-mt" ,"--moduletag", help="tag to be appended to output folder", type=str, default="")
    base_parser.add_argument("-o" ,"--outname", help="output name to be prepended to the output file name", type=str, default="pedestal")
    base_parser.add_argument("-D" ,"--outdir", help="output directory path where to save data", type=str, default="./")
    base_parser.add_argument("-da" ,"--disable-analysis", help="flag to disable analysis", action="store_true")
    base_parser.add_argument("-dt" ,"--disable-datataking", help="flag to disable datataking", action="store_true")
    base_parser.add_argument("-dbg" ,"--debug", help="flag to enable debug messages on console", action="store_true")
    base_parser.add_argument("-c" ,"--channel0", help="channel from which the analysis starts", type=int, default=0)
    base_parser.add_argument("-n" ,"--nchannels", help="number of channels to be analyzed starting from channel specified with -c option", type=int, default=64)
    base_parser.add_argument("-f" ,"--force", help="force calculation of intermediate calibration files", action="store_true")
    base_parser.add_argument("-SiPM" ,"--enable-sipm", help="enable SiPM", action="store_true")
    if sipm:
        base_parser.add_argument("--enable-hv", help="enable HV before daq", action="store_true")
        base_parser.add_argument("--disable-smart-channels", help="disable smart channels", nargs="+", type=int, default=None)
        base_parser.add_argument("--smart-dacs", help="DACs values for SMART channels. If a single value is provided, then all DACs are set to the same value, otherwise specify 64 values.", nargs="+", type=int, default=100)
        base_parser.add_argument("--smart-global", help="global registers (R,C,PZ) for SMART channels.", nargs=3, type=int, default=[0,0,63])

    if testing_mode:
        base_parser.add_argument("-vp" ,"--vped", help="Vped to use", type=int, default=1200)
        base_parser.add_argument("-b" ,"--nblocks", help="number of Blocks of 32 samples", type=int, default=8)
        base_parser.add_argument("-p" ,"--packets", help="number of packets per event", type=int, default=8)
        base_parser.add_argument("-l" ,"--length", help="acquisition time in seconds, ignored for hardsync pedestal", type=float, default=10)
        base_parser.add_argument("-t" ,"--triggertype", help="trigger type: 0=internal, 1=external, 2=hardsync", type=int, default=1)
        base_parser.add_argument("-d" ,"--triggerdelay", help="trigger delay", type=int, default=500)


    ped_parser = argparse.ArgumentParser(parents=[base_parser])
    ped_parser.add_argument("-fm" ,"--fast-mode", help="enable fast mode, i.e. disable extra plots", action="store_true")
    ped_parser.add_argument("-v" ,"--vpedscan", help="activate vped scan", action="store_true")
    if testing_mode:
        ped_parser.add_argument("--vpedvals", help="provide start, stop and step values vped scan", nargs="+", type=int, default=[4000])

    sig_parser = argparse.ArgumentParser(parents=[base_parser])
    sig_parser.add_argument("-ped" ,"--pedname", help="output name to be prepended to the pedestal file to perform calibration", type=str, default="pedestal")
    sig_parser.add_argument("-pdb" ,"--peddatabase", help="pedestal database file (including full path)", type=str, default=None)
    sig_parser.add_argument("-ptt" ,"--pedtrigtype", help="pedestal trigger type: 0=internal, 1=external, 2=hardsync, used to search for the correct file", type=int, default=2)
    sig_parser.add_argument("-s" ,"--signalscan", help="activate signal amplitude scan", action="store_true")

    if testing_mode:
        sig_parser.add_argument("--signalfreq", help="provide signal frequency in Hz", type=float, default=1113)
        sig_parser.add_argument("--signalvals", help="provide start, stop and step values for signal scan in Volt", nargs="+", type=float, default=[0.2])

    sig_sipm_parser = argparse.ArgumentParser(parents=[base_parser])
    sig_sipm_parser.add_argument("-ped" ,"--pedname", help="output name to be prepended to the pedestal file to perform calibration", type=str, default="pedestal")
    sig_sipm_parser.add_argument("-pdb" ,"--peddatabase", help="pedestal database file (including full path)", type=str, default=None)
    sig_sipm_parser.add_argument("-ptt" ,"--pedtrigtype", help="pedestal trigger type: 0=internal, 1=external, 2=hardsync, used to search for the correct file", type=int, default=2)
    sig_sipm_parser.add_argument("-s" ,"--signalscan", help="activate signal amplitude scan", action="store_true")
    sig_sipm_parser.add_argument("--enable-hv", help="enable HV in signal daq", action="store_true")
    sig_sipm_parser.add_argument("--disable-smart-channels", help="disable smart channels", nargs="+", type=int, default=None)
    sig_sipm_parser.add_argument("--smart-dacs", help="DACs values for SMART channels. If a single value is provided, then all DACs are set to the same value, otherwise specify 64 values.", nargs="+", type=int, default=100)
    sig_sipm_parser.add_argument("--smart-global", help="global registers (R,C,PZ) for SMART channels.", nargs=3, type=int, default=[0,0,63])


    trig_parser = argparse.ArgumentParser(parents=[base_parser])
    trig_parser.add_argument("-v" ,"--vpedscan", help="activate vped scan", action="store_true")
    trig_parser.add_argument("-gr" ,"--groupsrange", help="groups range", nargs="+", type=int)
    trig_parser.add_argument("--pmtref4vals", help="provide start, stop and step values for pmtref4 scan", nargs="+", type=int, default=None) ## to be checked
    trig_parser.add_argument("--threshvals", help="provide start, stop and step values for thresh scan", nargs="+", type=int, default=None) ## to be checked
    trig_parser.add_argument("-et" ,"--external-trigger", help="flag to enable the triggering from the external trigger line", action="store_true")
    if testing_mode:
        trig_parser.add_argument("--vpedvals", help="provide start, stop and step values vped scan", nargs="+", type=int, default=[4000])
        trig_parser.add_argument("-w" ,"--wbias", help="wbias default parameter", type=int, default=985)
        trig_parser.add_argument("-g" ,"--gain", help="trigger gain default value", type=int, default=0x15)
        trig_parser.add_argument("-pr" ,"--pmtref4", help="pmtref4 default value", type=int, default=1500)
        trig_parser.add_argument("-th" ,"--thresh", help="thresh default value", type=int, default=2000)

    power_parser = argparse.ArgumentParser(parents=[base_parser])
    peltier_parser = argparse.ArgumentParser(parents=[base_parser])
    smart_parser = argparse.ArgumentParser(parents=[base_parser])
    smart_parser.add_argument("--smart-dacs", help="DACs values for SMART channels. If a single value is provided, then all DACs are set to the same value, otherwise specify 64 values.", nargs="+", type=int, default=100)
    smart_parser.add_argument("--smart-global", help="global registers (R,C,PZ) for SMART channels.", nargs=3, type=int, default=[0,0,63])
    
    if key is None:
        myparser = base_parser
    elif key=="pedestal":
        myparser = ped_parser
    elif key=="signal":
        myparser = sig_parser
    elif key=="signal_sipm":
        myparser = sig_sipm_parser
    elif key=="trigger":
        myparser = trig_parser
    elif key=="power":
        myparser = power_parser
    elif key=="peltier":
        myparser = peltier_parser
    elif key=="smart":
        myparser = smart_parser
    else:
        raise ValueError("Keyword for argument parser not recognized.")
    
    return myparser


def get_outdir1(_module,_outdir, _moduletag ):
    moduleID = int(_module)
    outdir = _outdir+"/"
    if testing_mode:
        outdir += "testing/"
    outdir += "Module"+str(moduleID)
    if _moduletag!="":
        outdir += "_"+_moduletag
    outdir += "/"
    os.system("mkdir -p "+str(outdir))
    return outdir

def get_outdir(args):
    outdir = get_outdir1(args.module, args.outdir, args.moduletag)
    return outdir

def check_status_files(outdir, smart_flag=False):
    """Checks if the 'status.yaml' and 'status.html' files exist; if not it 
    creates them

    Args:
        outdir (str): Directory where status files are or will be stored
    """
    check_status_file_yaml(outdir=outdir, smart_flag=smart_flag)
    check_status_file_html(outdir=outdir, smart_flag=smart_flag)

def check_status_file_yaml(outdir, smart_flag=False):
    """Checks if the 'status.yaml' file exists; if not it creates it and 
    inizializes all the test results to False

    Args:
        outdir (str): Directory where "status.yaml" file is or will be stored
    """
    fname = os.path.join(outdir, "status.yaml")
    dstatus = {
        "power": None,
        "peltier": None,
        "pedestal": None,
        "signal": None,
        "linearity": None,
        "vpedscan": None,
        "triggerscan_thresh": None,
        "triggerscan_pmtref4": None
    }
    if smart_flag:
        dstatus["smart"] = None
    if not os.path.exists(fname):
        with open(fname, 'w') as outfile:
            yaml.dump(dstatus, outfile, default_flow_style=False)

def check_status_file_html(outdir, smart_flag=False):
    """Checks if the 'status.html' files exist; if not it creates it

    Args:
        outdir (str): Directory where "status.html" file is or will be stored
    """
    fname = os.path.join(outdir, "status.html")
    if not os.path.exists(fname):
        if not smart_flag:
            subprocess.run(["cp", "status.html", outdir])
        else:
            subprocess.run(["cp", "status_smart.html", outdir+"/status.html"])



def update_status_files(outdir, test, test_status):
    """Updates the 'status.yaml' and 'status.html' files

    Args:
        outdir (str): Directory where status files are stored
        test (str): test name
        test_status (bool): Test status: True if test is passed, False otherwise
    """
    update_status_file_yaml(outdir=outdir, test=test, test_status=test_status)
    update_status_file_html(outdir=outdir, test=test, test_status=test_status)


def update_status_file_yaml(outdir, test, test_status):
    """Updates the 'status.yaml' file

    Args:
        outdir (str): Directory where "status.yaml" file is stored
        test (str): test name
        test_status (bool): Test status: True if test is passed, False otherwise
    """    
    fname = os.path.join(outdir, "status.yaml")
    # Oper yaml file
    with open(fname, 'r') as ymlfile:
        dstatus = yaml.safe_load(ymlfile)
    # Update test
    dstatus[test] = test_status
    # Save yaml file
    with open(fname, 'w') as outfile:
        yaml.dump(dstatus, outfile, default_flow_style=False)


def update_status_file_html(outdir, test, test_status):
    """Updates the 'status.html' file

    Args:
        outdir (str): Directory where "status.html" file is stored
        test (str): test name
        test_status (bool): Test status: True if test is passed, False otherwise
    """
    fname = os.path.join(outdir, "status.html")

    with open(fname, 'r') as f:
        html_str = f.read()

    # Modify CSS
    colors = ["red", "green", "blue"]
    keys = ["", "a:link ", "a:visited "] # do not remove the space

    for c in colors:
        for k in keys:
            if(re.findall(".%s %s{color: %s;}" % (test, k, c), html_str)):
                html_str = html_str.replace(
                    ".%s %s{color: %s;}" % (test, k, c),
                    ".%s %s{color: %s;}" % (test, k, colors[int(test_status)])
                )
    
    # Modify Symbol
    symbols = [
        "&#10008;",  # FAIL
        "&#10004;",  # PASS
        "<b>&#63;</b>"  # NOT AVAILABLE
    ]
    for symbol in symbols:
        if(re.findall("%s <!-- %s -->" % (symbol, test), html_str)):
            html_str = html_str.replace(
                "%s <!-- %s -->" % (symbol, test),
                "%s <!-- %s -->" % (symbols[int(test_status)], test)
            )


    with open(fname, 'w') as f:
        html_str = f.write(html_str)
    


def set_status_hmtl_directory(outdir, key, subdir):
    fname = os.path.join(outdir, "status.html")

    with open(fname, "r") as f:
        html_str = f.read()

    html_str = html_str.replace(key, subdir)

    with open(fname, "w") as f:
        html_str = f.write(html_str)






def unique_filename(fname):
    basename = os.path.basename(fname)
    dirname = os.path.dirname(fname)
    i=0
    newname = basename
    while os.path.exists(dirname+"/"+newname):
        name,ext = os.path.splitext(newname)
        if name.endswith("_"+str(i)):
            name = name.replace("_"+str(i),"")
            i+=1
        newname = name+"_"+str(i)+ext

    return dirname+"/"+newname
'''
### Logging
TEST_LEVEL_INFO = 100
TEST_LEVEL_PASS = 110
TEST_LEVEL_FAIL = 120
def redirect_stdout(logfile='/dev/null'):
    sys.stdout.flush()
    local_stdout = os.dup(1)
    fileout = os.open(logfile, os.O_APPEND | os.O_CREAT | os.O_WRONLY)
    os.dup2(fileout,1)
    os.close(fileout)
    sys.stdout = os.fdopen(local_stdout,'w')

class LoggerWriter(logging.getLoggerClass()):
    def __init__(self, logname=None,logfile=None):
        super(LoggerWriter,self).__init__(logname,level=logging.NOTSET)
        
        logging.addLevelName(TEST_LEVEL_INFO, "TEST_INFO")
        logging.addLevelName(TEST_LEVEL_PASS, "TEST_PASS")
        logging.addLevelName(TEST_LEVEL_FAIL, "TEST_FAIL")
 
        if logname is not None and logfile is not None:
            self.setup(logname=logname,logfile=logfile)

    def setup(self,logname='mylog',logfile='mylog.log'):
        self.name = logname
        redirect_stdout(logfile=logfile)

        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.setLevel(TEST_LEVEL_INFO)
        self.file_handler = logging.FileHandler(logfile)
        self.file_handler.setLevel(logging.DEBUG)

        self.formatter = logging.Formatter('%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        self.file_handler.setFormatter(self.formatter)
        self.stdout_handler.setFormatter(self.formatter)

        self.addHandler(self.file_handler)
        self.addHandler(self.stdout_handler)


#global logger
#logger = 0
#def init_logger(logfile):
#    global logger
#    logger = LoggerWriter(logfile=unique_filename(logfile))
'''

##########

class MyInfo(dict):
    def __init__(self):
        super(MyInfo, self).__init__()
    def save_logfile(self, outname):
        with open(outname+".yaml","w") as fptr:
            yaml.dump(self, fptr, default_flow_style=False)
        with open(outname+".txt","w") as fptr:
            for k in self.keys():
                if type(self[k]) is list:
                    outstr = " ".join( [ str(x) for x in self[k]] )
                    fptr.write("{0}\t{1}\n".format(k,outstr))
                else:
                    fptr.write("{0}\t{1}\n".format(k,self[k]))


class MyOutput(pd.DataFrame):
    ## new_column : self["col"]=[vals], self["col"]=0.
    ## select_by_row: self.loc[self.Name=="Tom"]
    ## new_row : self.loc[i,"col1"] = val1
    ## fill_row : self.loc[self.Name=="Tom","col1"] = val1

    def __init__(self, **kwargs):
        super(MyOutput, self).__init__(**kwargs) 
        self.load_limits()
        self._easyStyler = Styler.from_custom_template("./", "template_html.tpl")
        self.mystyle = self._easyStyler(self)
        #self.mystyle = self.style
        self._float_fmt = ".3e"
        
    def _setup_style(self):
        self.mystyle.hide_index()
        self.mystyle.set_properties(**{'text-align': 'center'})
        
    def _set_bkg_color(self,s,flags):
        out= ['background-color: green' if f else 'background-color: red' for f in flags]
        return out
    
    def load_limits(self):
        ## load validity limits file
        fname = "limits.yaml"
        d={}
        with open(fname) as fptr:
            d = yaml.load(fptr, Loader=yaml.FullLoader)
        self._limits = d

    @property
    def limits(self):
        return self._limits
    @property
    def nrows(self):
        return len(self)
    @property
    def ncols(self):
        return len(self.columns)

    def set_types(self,types):
        dtypes = {self.columns[i]:types[i] for i in range(self.ncols)} 
        return MyOutput(data=self.astype(dtype=dtypes))

    def save_to_file(self, fname, sep=";", header=True, align_colnames=False):
        if align_colnames:
            if self.columns.nlevels>1:
                newcols = { name:"{:10}".format(name) for name in self.columns.levels[0] }
                tmp = self.rename(columns=newcols, level=0, inplace=False)
            else:
                newcols={ name:"{:10}".format(name) for name in self.columns}
                tmp = self.rename(columns=newcols, inplace=False)
            tmp.to_csv(fname,sep=sep, index=False, header=header, float_format="%"+self._float_fmt)
        else:
            self.to_csv(fname,sep=sep, index=False, header=header, float_format="%"+self._float_fmt)
        #with open(fname,'w') as fout:
        #    fout.write(self.__repr__())
        
    def _add_limits_to_output_minmax(self):#, idx=0):
        self.limits_min = []
        self.limits_max = []
        for col in self.columns:
            if col in self._limits.keys():
                #self.limits_min.append(self._limits[col][0])
                #self.limits_max.append(self._limits[col][1])
                self.limits_min.append(("{0:<10"+self._float_fmt+"}").format(self._limits[col][0]))
                self.limits_max.append(("{0:<10"+self._float_fmt+"}").format(self._limits[col][1]))
            else:
                self.limits_min.append("{:10}".format(np.nan))
                self.limits_max.append("{:10}".format(np.nan))
        #self.loc[len(self),self.columns]=limits_strings
        self.columns = pd.MultiIndex.from_tuples(zip(self.columns, self.limits_min, self.limits_max), names=[None,'Limits_min','Limits_max'])
        self.mystyle = self._easyStyler(self)

    def _add_limits_to_output_interval(self):#, idx=0):
        self.limits_strings = []
        for col in self.columns:
            if col in self._limits.keys():
                self.limits_strings.append("["+str(self._limits[col][0])+","+str(self._limits[col][1])+"]")
            else:
                self.limits_strings.append("")
        #self.loc[len(self),self.columns]=limits_strings
        self.columns = pd.MultiIndex.from_tuples(zip(self.columns, self.limits_strings), names=[None,'Limits'])
        self.mystyle = self._easyStyler(self)

        #df1 = self[0:idx]
        #df2 = self[idx:]
        #df1.loc[idx]=[-1]*self.ncols
        #df1.loc[idx+1]=[-1]*self.ncols
        #df_result = pd.concat([df1, df2])
        #df_result.index = [*range(df_result.shape[0])] 
        #self = MyOutput(data=df_result)
        #ped_output.loc[len(ped_output), columns] = limits

        #limits_min = []
        #limits_max = []
        #for col in self.columns:
        #    if col in self._limits.keys():
        #        limits_min.append(self._limits[col][0])
        #        limits_max.append(self._limits[col][1])
        #    else:
        #        limits_min.append("-")
        #        limits_max.append("-")
        #self.loc['min',self.columns] = limits_min
        #self.loc['max',self.columns] = limits_max

        return self

    def add_limits_to_output(self,mode="interval"):
        if mode=="interval":
            self._add_limits_to_output_interval()
        elif mode=="minmax":
            self._add_limits_to_output_minmax()
        else:
            raise ValueError("mode "+str(mode)+" is not valid for adding limits to output.")
            
    def _add_limits_to_html(self):
        if self.mystyle:
            caption = "Limits used: "
            for key in self._limits.keys():
                if key in self.columns:
                    caption += key + " ["+str(self._limits[key][0])+","+str(self._limits[key][1])+"]; "
            self.mystyle.set_caption(caption)
            _myst = [
                dict(selector="th", props=[("font-size", "120%"),
                                           ("text-align", "center")]),
                dict(selector="caption", props=[("caption-side", "top")])
            ]
            self.mystyle.set_table_styles(_myst)

    
    def save_to_html(self, fname, title="",add_limits=False):#, sep=";", header=True):
        #if add_limits:
        #    self._add_limits_to_html()
        if self.mystyle:
            #self.mystyle.hide_index()
            self._setup_style()
            html = self.mystyle.render(table_title=title)
        #else:
        #    html = self.to_html()
        with open(fname,"w") as fptr:
            fptr.write(html)
        return html

    def check_quality(self,colname, rows=None):
        """Checks if the values in the column 'colname' are within the validity 
        ranges. Returns flags for valid rows. If this column is not in the 
        validity ranges file, nothing is done. If row is specified 
        (int or list of int), the check is done for this row only."""
        if colname not in self._limits.keys():
            return None
        xmin, xmax = self._limits[colname][0], self._limits[colname][-1]
        if len(self._limits[colname])>2:
            ## case with warning edges
            xmin_w, xmax_w = self._limits[colname][1], self._limits[colname][2]
        else:
            xmin_w, xmax_w = xmin, xmax

        if rows is None:
            colname1 = self.columns[self.columns.get_level_values(0)==colname][0]
            flags = (self[colname1]>=xmin) & (self[colname1]<=xmax)
            #flags = (self.loc[:,pd.IndexSlice[colname,:]]>=xmin) & (self.loc[:,pd.IndexSlice[colname,:]]<=xmax)
            #self.mystyle = self.mystyle.apply(self._set_bkg_color, flags=flags, subset=[colname])
            self.mystyle = self.mystyle.apply(self._set_bkg_color, flags=flags, subset=pd.IndexSlice[:,colname1])
            #self.mystyle = self.mystyle.apply(self._set_bkg_color, flags=flags, subset=pd.IndexSlice[:,pd.IndexSlice[colname,:]])
        else:
            flags = flags1 = (self.loc[rows,colname]>=xmin) & (self.loc[rows,colname]<=xmax)
            #try:
            #    tmp = self.loc[rows,colname].astype(dtypes=['float32'])
            #except:
            #    tmp = self.loc[rows,colname]
            #print (tmp)
            #flags = flags1 = (tmp>=xmin) & (tmp<=xmax)
            try:
                for f in flags1:
                    pass
            except TypeError:
                flags1 = [flags1]
            self.mystyle = self.mystyle.apply(self._set_bkg_color, flags=flags1, subset=pd.IndexSlice[rows,colname])
            #self.style.apply(self._set_bkg_color, flags=flags1, subset=pd.IndexSlice[rows,colname])
        return flags


class MultipagePdf:
    def __init__(self, unit='pt',outname="mypdf.pdf"):
        self.outname = outname
        self.pdf = FPDF(unit=unit)

    def save_to_file(self, outname=None):
        if outname is not None:
            self.outname = outname
        self.pdf.output(self.outname, "F")
    
    """    
    def _get_nx_ny(self, n, nx=None, ny=None):
        if nx is not None and ny is not None:
            nx = int(nx)
            ny = int(ny)
        if nx is not None and ny is None:
            nx = int(nx)
            tmp_n = int(n/nx)
            if tmp_n*nx==n:
                ny = tmp_n
            else:
                ny = tmp_n+1
        if nx is None and ny is not None:
            ny = int(ny)
            tmp_n = int(n/ny)
            if tmp_n*ny==n:
                nx = tmp_n
            else:
                ny = tmp_n+1
        if nx is None and ny is None:
            tmp_n = int(n**0.5)
            if tmp_n**2 == n:
                nx=ny=tmp_n
            else:
                nx=tmp_n
                ny=int(n/tmp_n)
        return nx,ny
    """
    def _get_nx_ny(self, n, nx=None, ny=None):
        
        if nx is not None and ny is not None:
            nx = int(nx)
            ny = int(ny)
            
        if nx is not None and ny is None:
            nx = int(nx)
            tmp_n = n//nx
            if tmp_n*nx==n:
                ny = tmp_n
            else:
                ny = tmp_n+1
        if nx is None and ny is not None:
            ny = int(ny)
            tmp_n = n//ny
            if tmp_n*ny==n:
                nx = tmp_n
            else:
                nx = tmp_n+1
        if nx is None and ny is None:
            nx = int((n**0.5))
            tmp_n = n//nx
            if tmp_n*nx==n:
                ny=tmp_n
            else:
                ny=tmp_n+1
        return nx,ny

    def add_page_figures(self,fig_list, nx=None, ny=None):
        nfig = len(fig_list)
        if nfig==0:
            return
        nx , ny = self._get_nx_ny(nfig, nx=nx, ny=ny)
        w = []
        h = []

        for fig in fig_list:
            _w,_h = Image.open(fig).size
            w.append(_w)
            h.append(_h)
        w2d=np.zeros((nx,ny))
        h2d=np.zeros((nx,ny))
        for i in range(nx):
            for j in range(ny):
                k = i*nx+j
                if k<nfig:
                    w2d[i,j] = w[k]
                    h2d[i,j] = h[k]
        w_rows = w2d.sum(axis=1)
        h_cols = h2d.sum(axis=0)
        tot_w = max(w_rows)
        tot_h = max(h_cols)

        self.pdf.add_page(format=[tot_w, tot_h])
        for i in range(nx):
            for j in range(ny):
                k = i*nx+j
                if k<nfig:
                    self.pdf.image(fig_list[k], np.sum(w2d[i,:j]), np.sum(h2d[:i,j]) )
        
