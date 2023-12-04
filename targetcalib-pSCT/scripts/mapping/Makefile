
CC = g++
LDFLAGS = `root-config --cflags --libs` -Wl,-rpath,${TARGETDRIVERPATH}/lib -lTargetDriver -Wl,-rpath,${TARGETCALIBPATH}/lib -lTargetCalib
#-lMathMore
LIB = -L${TARGETDRIVERPATH}/lib -L${TARGETCALIBPATH}/lib
INC = -I${TARGETDRIVERPATH}/include/ -I${TARGETCALIBPATH}/include/


plot_data_tc: plot_data_tc.cc
	$(CC) -o plot_data_tc plot_data_tc.cc $(INC) $(LDFLAGS) $(LIB)
