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
py.test -n2 --boxed rdc_test.py

# run tests
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
