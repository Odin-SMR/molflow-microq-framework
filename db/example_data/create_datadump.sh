# The password prompt is swallowed by the pipe and removed by awk.
# Just type the mysql password.

docker exec -it uservice_mysqlhost_1 mysqldump --skip-opt -u uservice --password smr jobs_QSMRVDS --where="type='qsmr' limit 1000" | awk '{if (NR > 1) print $0}' > uservice_dump.sql

docker exec -it uservice_mysqlhost_1 mysqldump --skip-opt -u uservice --password smr projects | awk '{if (NR > 1) print $0}' >> uservice_dump.sql
