#!/run/current-system/sw/bin/bash

# create inside our directory that we created as `mongodb`
# the following directories which saves the data and log of the mongo service
mkdir -p ./mongodb/var/lib/mongo/
mkdir -p ./mongodb/var/log/mongodb/

# run the mongo daemon with the configuration that we have created above
mongod --config ./mongodb/mongo.conf

