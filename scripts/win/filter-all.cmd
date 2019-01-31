cd ..
cd "data for scripts"
cd vakantie-j
call %~dp0\filter-log.cmd
cd ..
cd vakantie-r
call %~dp0\filter-log.cmd
cd ..
cd vakantie-rtor
call %~dp0\filter-log.cmd
cd ..

pause
