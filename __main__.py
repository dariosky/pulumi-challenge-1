"""An AWS Python Pulumi program"""
import json
import mimetypes
import os

import pulumi
import pulumi_aws as aws
from pulumi_aws import s3

environment = pulumi.get_stack()
long_env_tag = {
    'dev': 'Development',
    'prod': 'Production'
}.get(environment)


def public_read_policy_for_bucket(bucket_name):
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}/*",
            ]
        }]
    })


bucket = aws.s3.Bucket("pulumi-challenge-1-bucket",
                       acl="public-read",
                       tags={
                           "Environment": long_env_tag,
                           "Name": "Public site for Pulumi Challenge",
                       },
                       website=aws.s3.BucketWebsiteArgs(
                           index_document="index.html",
                           error_document="error.html",
                       ))
bucket_name = bucket.id

bucket_policy = s3.BucketPolicy("bucket-policy",
    bucket=bucket_name,
    policy=bucket_name.apply(public_read_policy_for_bucket))

content_dir = "website"
for file in os.listdir(content_dir):
    filepath = os.path.join(content_dir, file)
    mime_type, _ = mimetypes.guess_type(filepath)
    obj = s3.BucketObject(file,
                          bucket=bucket.id,
                          source=pulumi.FileAsset(filepath),
                          content_type=mime_type)

s3_origin_id = 'pulumi-challenge-origin'
cloudfront_distribution = aws.cloudfront.Distribution(
    'pulumi-challenge',
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=bucket.bucket_regional_domain_name,
        origin_id=s3_origin_id,
        s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
            origin_access_identity=aws.cloudfront.OriginAccessIdentity(
                'origin-access-identity-pulumi-challenge-1',
                comment='Pulumi challenge #1'
            ).cloudfront_access_identity_path,
        ),
    )],
    enabled=True,
    is_ipv6_enabled=True,
    comment="Pulumi challenge #1",
    default_root_object="index.html",
    # logging_config=aws.cloudfront.DistributionLoggingConfigArgs(
    #     include_cookies=False,
    #     bucket="mylogs.s3.amazonaws.com",
    #     prefix="myprefix",
    # ),
    # aliases=[
    #     "mysite.example.com",
    #     "yoursite.example.com",
    # ],
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=[
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
        ],
        cached_methods=[
            "GET",
            "HEAD",
        ],
        target_origin_id=s3_origin_id,
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
        viewer_protocol_policy="allow-all",
        min_ttl=0,
        default_ttl=3600,
        max_ttl=86400,
    ),
    ordered_cache_behaviors=[
        # aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
        #     path_pattern="/content/immutable/*",
        #     allowed_methods=[
        #         "GET",
        #         "HEAD",
        #         "OPTIONS",
        #     ],
        #     cached_methods=[
        #         "GET",
        #         "HEAD",
        #         "OPTIONS",
        #     ],
        #     target_origin_id=s3_origin_id,
        #     forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
        #         query_string=False,
        #         headers=["Origin"],
        #         cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(
        #             forward="none",
        #         ),
        #     ),
        #     min_ttl=0,
        #     default_ttl=86400,
        #     max_ttl=31536000,
        #     compress=True,
        #     viewer_protocol_policy="redirect-to-https",
        # ),
        # aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
        #     path_pattern="/content/*",
        #     allowed_methods=[
        #         "GET",
        #         "HEAD",
        #         "OPTIONS",
        #     ],
        #     cached_methods=[
        #         "GET",
        #         "HEAD",
        #     ],
        #     target_origin_id=s3_origin_id,
        #     forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
        #         query_string=False,
        #         cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(
        #             forward="none",
        #         ),
        #     ),
        #     min_ttl=0,
        #     default_ttl=3600,
        #     max_ttl=86400,
        #     compress=True,
        #     viewer_protocol_policy="redirect-to-https",
        # ),
    ],
    price_class="PriceClass_100",
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
            locations=[],
        ),
    ),
    tags={
        "Environment": long_env_tag,
    },
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    )
)

# Export the name of the bucket
pulumi.export('readme', 'A stack to play with Pulumi - and solve the challenge #1')
pulumi.export('bucket_name', bucket.id)
pulumi.export('website_url', bucket.website_endpoint)
