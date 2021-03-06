import argparse
import json
import os

try:
    import urllib2
    from cStringIO import StringIO

    v = 2
except ImportError:
    import urllib.request, urllib.error, urllib.parse
    from io import StringIO

    v = 3


def handle_args():
    parser = argparse.ArgumentParser(description='Dumps Tables from InfluxDB and writes them to files')
    parser.add_argument('--url',
                        dest='url',
                        default='http://127.0.0.1:8086?/query?db=mydb',
                        help='URL to the InfluxDB with username, password... Default: http://127.0.0.1:8086/query?db=mydb',
                        type=str, )
    parser.add_argument('--file',
                        dest='file',
                        help='File with tablenames, one tablename per line',
                        default='',
                        type=str, )
    parser.add_argument('tablenames',
                        type=str,
                        nargs='*',
                        help='List of tabelnames')
    parser.add_argument('--target',
                        dest='target',
                        help='Target folder. Default: dump',
                        default='dump',
                        type=str, )
    return parser.parse_args()


def create_target_folder(target):
    if not os.path.exists(target):
        os.makedirs(target)


def build_tablename_list(file_name, tables):
    if file_name != '' and os.path.isfile(file_name) and os.access(file_name, os.R_OK):
        tables.extend([line.rstrip('\n') for line in open(file_name)])
    return tables


def raise_http_error(code, table):
    raise Exception('Got HTTP: %s for table: %s' % (code, table))


def query_data_for_table(url, table):
    table = table.replace("\\", "\\\\")
    url += '&format=json&epoch=ms&q='
    if v == 2:
        url += urllib2.quote('SELECT * FROM "%s"' % table)
        try:
            response = urllib2.urlopen(urllib2.Request(url))
        except urllib2.HTTPError as error:
            raise_http_error(error.code, table)
    elif v == 3:
        url += urllib.parse.quote('SELECT * FROM "%s"' % table)
        try:
            response = urllib.request.urlopen(urllib.request.Request(url))
        except urllib.error.HTTPError as error:
            raise_http_error(error.code, table)
    if response.code != 200:
        raise_http_error(error.code, table)
    if v == 2:
        json_object = json.loads(response.read())
    elif v == 3:
        json_object = json.loads(response.read().decode('utf8'))
    return convert_json_to_line_format(json_object)


def escape_for_influxdb(string):
    if not isinstance(string, str):
        string = str(string)
    return string.replace(' ', '\ ').replace(',', '\,')


def convert_json_to_line_format(json_object):
    if len(json_object['results']) == 0 or len(json_object['results'][0]) == 0:
        print("EMPTY RESULT!")
        return ""
    json_object = json_object['results'][0]['series'][0]
    tags = []
    for index, v in enumerate(json_object['columns']):
        if v != 'value' and v != 'time':
            tags.append((index, escape_for_influxdb(v)))
    time_index = json_object['columns'].index("time")
    value_index = json_object['columns'].index("value")
    data = StringIO()
    for value in json_object['values']:
        data.write(escape_for_influxdb(json_object['name']))
        for tag in tags:
            data.write(',')
            data.write(escape_for_influxdb(tag[1]))
            data.write('=')
            data.write(escape_for_influxdb(value[tag[0]]))
        data.write(' value=')
        if isinstance(value[value_index], unicode):
            data.write('"')
            data.write(value[value_index])
            data.write('"')
        else:
            data.write(escape_for_influxdb(value[value_index]))
        data.write(' ')
        data.write(str(value[time_index]))
        data.write('\n')
    return data.getvalue()


def write_data_to_file(data, target, filename):
    f = open(os.path.join(target, filename), 'w')
    f.write(data + '\n')
    f.close()


if __name__ == '__main__':
    args = handle_args()
    create_target_folder(args.target)
    i = 0
    print("The following tables were dumped:")
    for t in build_tablename_list(args.file, args.tablenames):
        result = query_data_for_table(args.url, t)
        if result:
            write_data_to_file(result, args.target, str(i) + ".txt")
        print(t)
        i += 1
