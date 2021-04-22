#  expectValue = "completed successfully"
#  scriptTimeout = 10
#  replayEnabled = false
#  replayTimeout = 0
bucket=`gsutil ls | grep '<STACK NAME>'`

# delete all files in bucket and delete bucket
gsutil -m rm -r ${bucket}

if [ $? -eq 0 ]; then
    echo "completed successfully"
fi
