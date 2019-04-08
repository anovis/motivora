#!/bin/bash
export AWS_PROFILE=chalice
export AWS_DEFAULT_REGION=us-east-1

# Should we include git tag?
if [ "$1" = "--git-tag" ]
  then
    # echo Checking out master and pulling down latest tag
    # git checkout master && git pull && git fetch --tags
    CURRENT_TAG=`git describe --abbrev=0 --tags`

    echo Enter the git version tag for this release in the following format: v1.0.0
    echo The current version tag is: $CURRENT_TAG
    echo
    read NEW_TAG

    echo Enter a release message for this release:
    echo
    read RELEASE_MESSAGE
fi

# Frontend
echo Deploying frontend app
echo
echo Running npm install, npm test, npm run build, pushing to S3, creating git tag and pushing to github

npm install && npm run build && aws s3 sync build/ s3://motivora-website

# Backend
echo
echo Deploying backend app

chalice deploy

# Push git tag to github
if [ "$1" = "--git-tag" ]
  then
    git tag $NEW_TAG -m "$RELEASE_MESSAGE" && git push origin $NEW_TAG
fi
