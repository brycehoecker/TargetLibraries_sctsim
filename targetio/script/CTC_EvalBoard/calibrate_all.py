import os

path="/DATA/Messungen_Adrian/CTC_Eval_Board/TC_and_T5TEA/ped_stability/data/"

#for i in range(0,17):
    #command="generate_ped -i data/fix8_file_restart_{}_r0.tio -o data/fix8_file_restart_{}_ped.tcal -n 100".format(i,i)
    #command="generate_ped -i data/fix10_ped_restart_{}_r0.tio -o data/fix10_ped_restart_{}_ped.tcal".format(i,i)
    #os.system(command)
#

for i in range(50,51):
 #for i in ([3,5,7,8]):
     for j in range(0,85):
     #for j in ([3,5,7,8]):
#         command="apply_calibration -i data/fix10_file_restart_{}_r0.tio -p data/fix10_ped_restart_{}_ped.tcal -o data/fix10_file_i{}_p{}_r1.tio".format(i,j,i,j)
         command="apply_calibration -i {}fix11_file_restart_{}_r0.tio -p {}fix11_ped_restart_{}_ped.tcal -o {}fix11_file_i{}_p{}_r1.tio".format(path,j,path,i,path,j,i)
         os.system(command)

#for i in range(0,16):
#    command="apply_calibration -i data/fix8_file_restart_{}_r0.tio -p data/fix8_file_restart_{}_ped.tcal ".format(i,i)
#    os.system(command)
