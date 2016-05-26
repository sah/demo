#!/bin/bash

# deploy and keep track of pid
echo "Deploying via SimpleHTTPServer..."
python -m SimpleHTTPServer &
FOO_PID=$!
sleep 3

PATH=$PATH:~/.local/bin
#wget https://bootstrap.pypa.io/get-pip.py
#python get-pip.py --user
#pip install --user virtualenv
#virtualenv sah_venv

source sah_venv/bin/activate
pip install -r requirements.txt

# run tests
echo "Running Functional Tests using py.test"
if py.test -n50 --boxed demo_tests.py realdev_app_demo_tests.py ; then
    # shut down server
    kill $FOO_PID
    # return appropriate exit code
    exit 0
else
    # shut down server
    kill $FOO_PID
    # return appropriate exit code
    exit 1
fi


echo "Running Functional Tests using Protractor"
if ./node_modules/.bin/protractor conf.js ; then
    # shut down server
    kill $FOO_PID
    # return appropriate exit code
    exit 0
else
    # shut down server
    kill $FOO_PID
    # return appropriate exit code
    exit 1
fi
