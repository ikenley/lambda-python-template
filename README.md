# lambda-python-template

Template for a small (no dependencies, no complex logic) Lambda Function written in Python

Lambda Functions have two sustainable equilibria:

1. Small:
   - Quick and dirty
   - A few lines of code that would fit in one `function.py` module
   - Zero external dependencies
   - 30 years ago these would have been Perl scripts
   - Managed via a zip archive in an S3 bucket
   - These tend to solve jobs like "when an S3 object drops, publish a message to an SQS queue"
2. Big:
   - Fully featured services, with tests, a boostrapping service, etc.
   - Similar to a large REST API, except it uses a Lambda event for an entry point rather than a controller
   - External package dependencies
   - Managed via a Docker image that extends the base Lambda image
   - These exist because a Lambda hook is the only option available (e.g. Cognito event hook)
   - For an example of this, see [https://github.com/ikenley/ai-app](https://github.com/ikenley/ai-app)

This repository has boilerplate code for (1), the quick-and-dirty function.

---

## Getting Started Locally

https://developer.nytimes.com/docs/most-popular-product/1/overview

```
python3 -m pip install --user virtualenv
sudo apt install python3-virtualenv
source ./.venv/bin/activate
cp env.example.sh env.sh
make hello_world_local
```

---

## Infrasctructure as Code (IaC)

This project uses Terraform to manage the cloud infrastructure (both the AWS resources and the CI/CD system).

```
cd terraform/projects/dev
terraform init
terraform apply
```

---

## Ad hoc scripting

```
aws s3api list-objects --bucket my-data-lake --prefix "news/nytimes/mostpopular/emailed/1/2023"
```

Workflow 2
