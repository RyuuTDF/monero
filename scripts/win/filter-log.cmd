@mkdir all
@mkdir inc
@mkdir out
cd inc
py ..\..\..\..\monero\scripts\log_filter.py ..\logdata.log addr.csv connect.csv notify.csv block.csv INC
cd ..
cd out
py ..\..\..\..\monero\scripts\log_filter.py ..\logdata.log addr.csv connect.csv notify.csv block.csv OUT
cd ..
cd all
py ..\..\..\..\monero\scripts\log_filter.py ..\logdata.log addr.csv connect.csv notify.csv block.csv
cd ..