#!/bin/sh

# defaults to minor version bump
ARGS=$*
if [ -z "$ARGS" ]; then
    ARGS=minor
fi

# run the python 'bumpversion' command
/usr/bin/env bumpversion $ARGS

# ensure it succeeded, or else bail out
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "Bump version succeeded"
else
    echo "Bump version failed"
    exit 1
fi

# get the build number from the git commit count
BUILD=$(git rev-list HEAD --count)

# get the branch
BRANCH=$(git branch | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/')

# get the major/minor version from the git tag and parse it
VERSION=$(git describe --long --tags | sed -E 's/^v([0-9]*)\.([0-9]*)\.[0-9]*-([0-9]*)-(.*)$/\1.\2.\3.\4/')
IFS='.' read -a versionparts <<< "$VERSION"

MAJOR=${versionparts[0]}
if [ -z "$MAJOR" ]; then
    MAJOR=0
fi

MINOR=${versionparts[1]}
if [ -z "$MINOR" ]; then
    MINOR=0
fi

OFFSET=${versionparts[2]}
if [ -z "$OFFSET" ]; then
    OFFSET=0
fi

HASH=${versionparts[3]}

if [ -z "$MAJOR" ]; then
    MAJOR=0
fi

echo "Version: $VERSION"
echo "Major: $MAJOR"
echo "Minor: $MINOR"
echo "Build: $BUILD"
echo "Branch: $BRANCH"
echo "Offset: $OFFSET"
echo "Hash: $HASH"
