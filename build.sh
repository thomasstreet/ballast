#!/bin/sh

# build the wheelhouse if it doesn't already exist
if [ ! -d ".wheelhouse" ]; then

    /usr/bin/env pip install wheelhouse
    /usr/bin/env wheelhouse build

    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        echo "Generate wheelhouse succeeded"
    else
        echo "Generate wheelhouse failed"
        exit 1
    fi
fi

# update the version from git branch info
/usr/bin/env python setup.py version --sha

RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Generate version succeeded"
else
    echo "Generate version failed"
    exit 1
fi

# run tox for code checks
/usr/bin/env tox -e py27

RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Code checks succeeded"
else
    echo "Code checks failed"
    exit 1
fi

# build the source distribution
/usr/bin/env python setup.py sdist bdist_wheel

RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Generate distribution succeeded"
else
    echo "Generate distribution failed"
    exit 1
fi
