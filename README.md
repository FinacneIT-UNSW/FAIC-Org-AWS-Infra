# Fintech Artificial Inteligence Consortium LAB AWS Infrastrucure

The Fintech Artificial Inteligence Consortium LAB is an UNSW vistual lab.

This is it's global aws infrastrucure (Datalake etc.). It must not be deployed multiple time!

## Important consideration

The state of the terraform configuration is saved to an S3 bucket.

<span style="color:red">**DO NOT CHANGE THE S3BACKEND CONFIGUARTION!**</span>
you will most likely destroy the infrastructure and lost some data...

## How to use?

Please, learn how to use terraform and how AWS works before doing anything...

1. Configure your AWS credentials, refer to [provider documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration), **do not hard code your secret token**.

2. Modify the infrastructure definition.

3. run `make` in the console. **Double check the terraform plan** before accepting the changes.

    3.1 Depending on your os, you might need to run `pipenv shell`

4. Check the outputs.json file to find API url and API keys.

## Commands

- `make zip_lambdas`: compress lambdas code
- `make deploy`: deploy stack
- `make output`: write outputs to outputs.json
- `make destroy`: destroy the stack (bad idea)

## Modifying the stack

Few considerations when it comes to modifying the stack.

1. All lambdas code goes to `/src/code`
2. Define global policies in the `policies` module
3. Do not add to much abstraction, keep things simple
4. One module = one functionality (exemple: datalake, docker orchestration, sagemaker env etc.), do not split resources belongings to same functionality (Datalake API go with the actual Datalake definition)


<span style="color:red">**There is no ctrl-z in terraform and AWS**</span>