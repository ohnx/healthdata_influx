import argparse
import dateutil
from lxml import etree
from influxdb import InfluxDBClient


def upload(host, data):
    client = InfluxDBClient(host=host, port=8086, database='health')
    client.create_database('health')
    client.write_points(points=data, batch_size=1000)

def parse(export):
    with open(export) as f:
        tree = etree.parse(f)

    formattedData = []
    records = tree.findall('Record')

    # we only want records with numeric values
    records = list(filter(lambda x: str(x.get('value')).isdigit(), records))

    for record in records:
        attr = record.attrib

        unit = attr['unit']
        value = attr['value']
        date = attr['endDate']
        source = attr['sourceName']
        measurement = _sanitize(attr['type'])

        time = dateutil.parser.parse(date).strftime('%Y-%m-%dT%H:%M:%SZ')

        recordDict = {
            'measurement': measurement,
            'tags': {},
            'time': time,
            'fields': {
                'value': value
            }
        }

        if unit is not None:
            recordDict['tags']['unit'] = _sanitize(unit)

        if source is not None:
            recordDict['tags']['source'] = _sanitize(source)

        formattedData.append(recordDict)

    print formattedData

    # return formattedData

def _sanitize(string):
    if string is not None:
        # for some reason it can't handle Unicode
        # replace some known offenders and as a last resort ignore chars that would raise
        return str(string
            .replace(u"\u2019", "'")
            .replace(u'\xa0', u' ')
            .encode('ascii', 'ignore')
        )
    else:
        raise

def main(host, export):
    try:
        data = parse(export)
        upload(host, data)

        print 'Total upload success!'
    except Exception as e:
        print 'Failure!'
        print str(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Uploads HealthKit data to InfluxDB')
    parser.add_argument('dbhost', help='InfluxDB host')
    parser.add_argument('file', help='Health data export file')

    args = parser.parse_args()

    main(args.dbhost, args.file)