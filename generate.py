#!/usr/bin/python

import botocore
import boto3
import sys
import random
import datetime


def log(logfile, msg):
    logfile.write("[" + str(datetime.datetime.utcnow()) + "] " + msg)

if len(sys.argv) < 3:
    sys.exit("Usage: \n\t python generate.py <duplication_factor> <orig_file> \n")
else:
    dupl_factor = int(sys.argv[1])
    orig_file = sys.argv[2]

s3 = boto3.resource('s3')
buck_name = 'network-traffic'
bucket = s3.Bucket(buck_name)
lg = open('generation.log', 'a')

exists = True
try:
    s3.meta.client.head_bucket(Bucket=buck_name)
except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
    error_code = int(e.response['Error']['Code'])
    if error_code == 404:
        exists = False

if exists:
    log(lg, 'bucket: %s found ' % buck_name + "\n")
else:
    log(lg, 'Error! Bucket: %s not found ' % buck_name)
    lg.close()
    sys.exit('Error! Bucket: %s not found ' % buck_name)

try:
    data = open(orig_file, 'r')
    ct = 0
    curr_file = None
    s3obj = None
    to_skip = (1, 2, 3, 6, 11, 20, 21, 22, 41)
    new_name = None

    for record in data:

        # Every 10K records create a new local file and a new S3 object
        if ct % 10000 == 0:
            if curr_file and new_name:
                # flush records to s3
                try:
                    s3obj = s3.Object(buck_name, new_name)
                    s3obj.put(Body=open(new_name, 'r'))
                except Exception:
                    log(lg, 'Failed to create s3 object, ' + new_name + '.')
                    lg.close()
                    sys.exit('Failed to create s3 object, ' + new_name + '.')

        new_name = "/home/ec2-user/data/chunk_%d" % (ct / 10000)
        if curr_file:
            curr_file.close()
        curr_file = open(new_name, 'w')

        for j in xrange(0, dupl_factor):
            ct += 1
            spl = record.strip().split(' ')
            to_send = ''

            # Gently perturb data with small modifications
            try:
                for k in xrange(0, 42):
                    if k not in to_skip:
                        if isinstance(spl[k], float):
                            spl[k] = min(1, max(0, float(spl[k]) + random.randint(-1, 1) * 0.01))
                        else:
                            spl[k] = max(0, int(spl[k]) + random.randint(-1, 1) * int(spl[k]) / 10)
            except Exception:
                log(lg, 'Malformed record aborted.' + "\n")
                continue

            for field in spl:
                if isinstance(field, float):
                    to_send += ',' + "%.2f" % field
                else:
                    to_send = to_send + ' ' + str(field)

            to_send = to_send[1:] + "\n"
except Exception:
    log(lg, 'Exception caught at top level. Exiting.')
    lg.close()
lg.close()
