#!/usr/bin/env bash
set -euo pipefail

STACK=${1:?usage: ./deploy.sh <stack-name>}
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
TAG=${TAG:-$(date +%Y%m%d-%H%M%S)}

# 1. infrastructure first, with 0 tasks (the image does not exist yet)
if ! aws cloudformation describe-stacks --stack-name "$STACK" >/dev/null 2>&1; then
  aws cloudformation deploy --stack-name "$STACK" --template-file template.yaml \
    --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
    --parameter-overrides Env=dev DesiredCount=0 ImageTag=initial
fi

# 2. build and push the image to the ECR repository created by the stack
REPO=$(aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='RepoUri'].OutputValue" --output text)
aws ecr get-login-password | docker login --username AWS --password-stdin "${REPO%%/*}"
docker build -t "$REPO:$TAG" app/
docker push "$REPO:$TAG"

# 3. run 2 tasks with the new image tag
aws cloudformation deploy --stack-name "$STACK" --template-file template.yaml \
  --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
  --parameter-overrides Env=dev DesiredCount=2 ImageTag="$TAG"

aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='AlbUrl'].OutputValue" --output text
