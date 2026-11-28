# SIS 3: Orders system as code

POST /orders (ECS Fargate behind an ALB) -> SNS -> SQS (+DLQ) -> idempotent Lambda -> DynamoDB.
Everything is in `template.yaml` (CloudFormation). No secrets in the repository.

## Deploy (AWS CloudShell, region us-east-1; needs AWS CLI and Docker)

    ./deploy.sh <stack-name>

The script creates the stack, builds and pushes the image, then runs 2 tasks.
It prints the service URL.

## Test

    curl $URL/health
    curl -X POST $URL/orders -d '{"orderId":"o-1","total":10}'

## Delete

    aws cloudformation delete-stack --stack-name <stack-name>

## Design notes
- Queue: maxReceiveCount 5, DLQ retention 14 days, visibility timeout 60 s (6 x 10 s function timeout).
- Idempotency key: `orderId` in table ProcessedTable (conditional write in one transaction with the counter).
- ECR: immutable tags, lifecycle policy (keep last 5 images), scan on push.
- Two roles: ExecutionRole (pull image, write logs) and TaskRole (sns:Publish only).
- Logs: CloudWatch, 7-day retention.
- No hard-coded resource names, so a second copy can be deployed under a new stack name.
- Tasks run in public subnets (no NAT gateway) to avoid cost; production would use private subnets with NAT or VPC endpoints.
Deployed by GitHub Actions
