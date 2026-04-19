from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_secretsmanager as secretsmanager,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    RemovalPolicy
)

class ThresholdStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. VPC (Multi-AZ)
        vpc = ec2.Vpc(self, "ThresholdVpc", max_azs=2)

        # 2. S3 Data Lake (Landing Zone)
        data_lake = s3.Bucket(self, "ThresholdDataLake",
            bucket_name="threshold-data-lake-2025-v2",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # 3. SQS DLQ
        dlq = sqs.Queue(self, "ThresholdDLQ")

        # 4. Lambda Validation Pipeline
        validation_lambda = _lambda.Function(self, "ValidationLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_src"),
            handler="ingest_handler.handler",
            environment={
                "BUCKET_NAME": data_lake.bucket_name
            }
        )
        data_lake.grant_read_write(validation_lambda)

        # 5. Secrets Manager
        secret = secretsmanager.Secret(self, "ThresholdSecrets",
            secret_name="threshold/api_keys",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="REPLACE_ME"
            )
        )

        # 6. ECS Fargate Backend (FastAPI)
        cluster = ecs.Cluster(self, "ThresholdCluster", vpc=vpc)
        backend_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "ThresholdBackend",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("../", file="backend/Dockerfile"),
                container_port=8000,
                secrets={
                    "STRIPE_SECRET_KEY": ecs.Secret.from_secrets_manager(secret, "STRIPE_SECRET_KEY"),
                    "GEMINI_API_KEY": ecs.Secret.from_secrets_manager(secret, "GEMINI_API_KEY"),
                    "ELEVENLABS_API_KEY": ecs.Secret.from_secrets_manager(secret, "ELEVENLABS_API_KEY")
                }
            ),
            public_load_balancer=True
        )

        # 7. S3 Frontend Hosting
        frontend_bucket = s3.Bucket(self, "ThresholdFrontend",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        s3deploy.BucketDeployment(self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../frontend/dist")],
            destination_bucket=frontend_bucket
        )

        # 8. SageMaker Serverless Inference Container
        # We define a Serverless inference endpoint to host threshold_net_best.pt 
        sagemaker_model = sagemaker.CfnModel(self, "ThresholdModelConfig",
            execution_role_arn=validation_lambda.role.role_arn, # Using lambda role for simplification
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image="763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference:1.12.0-cpu-py38", 
                mode="SingleModel",
                model_data_url=f"s3://{data_lake.bucket_name}/ml/threshold_net_best.tar.gz"
            )
        )
        sagemaker_endpoint_config = sagemaker.CfnEndpointConfig(self, "ThresholdEndpointConfig",
            production_variants=[sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                initial_variant_weight=1.0,
                model_name=sagemaker_model.attr_model_name,
                variant_name="AllTraffic",
                serverless_config=sagemaker.CfnEndpointConfig.ServerlessConfigProperty(
                    max_concurrency=5,
                    memory_size_in_mb=2048
                )
            )]
        )
        sagemaker_endpoint = sagemaker.CfnEndpoint(self, "ThresholdSageMakerEndpoint",
            endpoint_config_name=sagemaker_endpoint_config.attr_endpoint_config_name
        )

        # Outputs
        cdk.CfnOutput(self, "BackendAPIUrl", value=backend_service.load_balancer.load_balancer_dns_name)
        cdk.CfnOutput(self, "FrontendUrl", value=frontend_bucket.bucket_website_url)
