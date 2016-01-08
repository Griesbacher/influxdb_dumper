# InfluxDB Dumper
Dumps tables from InfluxDB to files in the InfluxDB lineformat. These files can later be imported by Nagflux or directly send by curl to the InfluxDB.

**This file should work with Python 2 and 3.**

## Usage
```
usage: dumper.py [-h] [--url URL] [--file FILE] [--target TARGET]
                 [tablenames [tablenames ...]]

Dumps Tables from InfluxDB and writes them to files

positional arguments:
  tablenames       List of tabelnames

optional arguments:
  -h, --help       show this help message and exit
  --url URL        URL to the InfluxDB with username, password... Default:
                   http://127.0.0.1:8086/query?db=mydb
  --file FILE      File with tablenames, one tablename per line
  --target TARGET  Target folder. Default: dump
```
### Get tablenames
``` bash
$ influx -database mydb -execute 'show series' | grep "name: " | cut -c 7-
```
Store them in a file and pass the filepath with --file to the dumper.

### Example
``` bash
$ influx -database mydb -execute 'show series' | grep "name: " | cut -c 7- > influx_list
$ python dumper.py --file influx_list --url 'http://InfluxDB:8086/query?db=mydb'
```
There should be a folder called dump, within on file per table.

Or dump just a few tables:
``` bash
$ python dumper.py --url 'http://InfluxDB:8086/query?db=mydb' 'mySpecialTable1' 'mySpecialTable2'
```
