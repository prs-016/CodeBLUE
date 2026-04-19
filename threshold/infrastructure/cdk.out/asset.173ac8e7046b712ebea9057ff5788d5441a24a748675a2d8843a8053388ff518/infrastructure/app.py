#!/usr/bin/env python3
import os
import aws_cdk as cdk
from threshold_stack import ThresholdStack

app = cdk.App()
ThresholdStack(app, "ThresholdStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT', '140219385716'), 
        region=os.getenv('CDK_DEFAULT_REGION', 'us-west-2')
    )
)

app.synth()
