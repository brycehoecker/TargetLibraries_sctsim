/sbin/ifconfig
/wr/bin/rtu_stat

#/wr/bin/rtu_stat add 08:00:56:00:03:51 11 0 0  ##Module 100
/wr/bin/rtu_stat add 08:00:56:00:03:24 4 0 0  ##Module 112 
/wr/bin/rtu_stat add 08:00:56:00:03:15 10 0 0  ##Module 113 
/wr/bin/rtu_stat add 08:00:56:00:03:9d 5 0 0  ##Module 114
/wr/bin/rtu_stat add 08:00:56:00:03:6d 9 0 0  ##Module 123 
/wr/bin/rtu_stat add 08:00:56:00:03:72 6 0 0  ##Module 124
/wr/bin/rtu_stat add 08:00:56:00:03:83 12 0 0  ##Module 128



#assign MAC addr for wr in 1st DACQ board
/wr/bin/rtu_stat add 02:34:56:78:9B:02 2 0 0	
/wr/bin/rtu_stat add 02:34:56:78:9B:03 3 0 0	#port 31
/wr/bin/rtu_stat add 02:34:56:78:9B:04 4 0 0	#port 26
/wr/bin/rtu_stat add 02:34:56:78:9B:05 5 0 0	#port 30
/wr/bin/rtu_stat add 02:34:56:78:9B:06 6 0 0	#port 25
/wr/bin/rtu_stat add 02:34:56:78:9B:07 7 0 0	#port 19
/wr/bin/rtu_stat add 02:34:56:78:9B:08 8 0 0	#port 29
/wr/bin/rtu_stat add 02:34:56:78:9B:09 9 0 0	#port 24
/wr/bin/rtu_stat add 02:34:56:78:9B:0a 10 0 0	#port 18
/wr/bin/rtu_stat add 02:34:56:78:9B:0b 11 0 0	#port 28
/wr/bin/rtu_stat add 02:34:56:78:9B:0c 12 0 0	#port 23
/wr/bin/rtu_stat add 02:34:56:78:9B:0d 13 0 0	#port 17
/wr/bin/rtu_stat add 02:34:56:78:9B:0e 14 0 0	#port 11
/wr/bin/rtu_stat add 02:34:56:78:9B:0f 15 0 0	
/wr/bin/rtu_stat add 02:34:56:78:9B:10 16 0 0	
/wr/bin/rtu_stat add 02:34:56:78:9B:11 17 0 0	
/wr/bin/rtu_stat add 02:34:56:78:9B:12 18 0 0

/wr/bin/rtu_stat add 02:34:56:78:9B:04 4 0 0
/sbin/ifconfig wr0 192.168.0.2

