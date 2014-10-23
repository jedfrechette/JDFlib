#!/bin/sh

# This will give you a nice list of all objects in the bucket with the bucket name stripped out
s3cmd ls -r s3://lidarguys-inactive-projects/BOE | awk '{print $4}' | sed 's#s3://<your-bucket-name>/##' > glacier-restore.txt

for x in `cat glacier-restore.txt`
do
    echo "restoring $x"
    aws s3api restore-object --restore-request Days=7 --bucket lidarguys-inactive-projects/BOE --key "$x"
done
