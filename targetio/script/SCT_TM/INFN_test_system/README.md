# INFN FEE QC

## Installation
0. Setup the **cta svn** environment. See section 4.1 in CTA_SWTOOLS.pdf document
1. Install **anaconda3**
2. Create the **cta-target** environment and activate it
    - `$ conda env create -f environment.yaml `
    - `$ conda activate cta-target`
3. Download **TARGET** libraries via svn (after having correctly set the private rsa key)
    - `$ cd /choose/your/path`
    - **TargetDriver**  
    `$ svn checkout svn+ssh://username@svn.in2p3.fr/cta/COM/CCC/ TargetDriver/trunk TargetDriver/trunk`
    - **TargetIO**  
    `$ svn checkout svn+ssh://username@svn.in2p3.fr/cta/COM/CCC/TargetIO/trunk TargetIO/trunk`
    - **TargetCalib**
        - Normal branch  
        `$ svn checkout svn+ssh://username@svn.in2p3.fr/cta/COM/CCC/TargetCalib/trunk TargetCalib/trunk`
        - pSCT branch  
        ` $ svn checkout svn+ssh://username@svn.in2p3.fr/cta/COM/CCC/TargetCalib/branches/pSCT TargetCalib/branches/pSCT`
4. Install **TargetDriver** 
    1. `$ cd TargetDriver/trunk`
    2. `$ mkdir BUILD`
    3. `$ cd BUILD`
    4. `$ cmake ../ -DPYTHON=ON -DCMAKE_INSTALL_PREFIX=$CONDA_PREFIX`
    5. `$ make`
    6. `$ make install`
    7. `$ cd ../../../`
5. Install **TargetIO**  
    1. `$ cd TargetIO/trunk`
    2. repeat 4.2 to 4.7
6. Install **TargetCalib**
    - Normal branch
        1. `$ cd TargetCalib/trunk` 
        2. repeat 4.2 to 4.6
    - pSCT branch
        1. `$ cd TargetCalib/branches/pSCT`
        2. repeat 4.2 to 4.6
