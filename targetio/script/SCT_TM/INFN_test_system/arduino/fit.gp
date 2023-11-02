set datafile separator ","; f(x) = a*(x + b); fit f(x) "calibration_clock.csv" u 4:2 via a,b

