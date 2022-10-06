import json
import mimetypes
import os

import pulumi
import pulumi_aws as aws
from pulumi_aws import s3


class CDNWebsite(pulumi.ComponentResource):
    @staticmethod
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

    def __init__(self, name, content_dir='website', opts=None) -> None:
        super().__init__("Static-CDN-Website", name, None, opts)

        self.environment = pulumi.get_stack()
        self.long_env_tag = {
            'dev': 'Development',
            'prod': 'Production'
        }.get(self.environment)

        self.bucket = aws.s3.Bucket(f"{name}-bucket",
                                    acl="public-read",
                                    tags={
                                        "Environment": self.long_env_tag,
                                        "Name": "S3 static content for a website",
                                    },
                                    website=aws.s3.BucketWebsiteArgs(
                                        index_document="index.html",
                                        error_document="error.html",
                                    ))
        bucket_name = self.bucket.id

        bucket_policy = s3.BucketPolicy("bucket-policy",
                                        bucket=bucket_name,
                                        policy=bucket_name.apply(self.public_read_policy_for_bucket))

        for file in os.listdir(content_dir):
            filepath = os.path.join(content_dir, file)
            mime_type, _ = mimetypes.guess_type(filepath)
            obj = s3.BucketObject(file,
                                  bucket=self.bucket.id,
                                  source=pulumi.FileAsset(filepath),
                                  content_type=mime_type)
        s3_origin_id = f'{name}-origin'
        self.cloudfront_distribution = aws.cloudfront.Distribution(
            name,
            origins=[aws.cloudfront.DistributionOriginArgs(
                domain_name=self.bucket.bucket_regional_domain_name,
                origin_id=s3_origin_id,
                s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                    origin_access_identity=aws.cloudfront.OriginAccessIdentity(
                        f'origin-access-identity-{name}',
                    ).cloudfront_access_identity_path,
                ),
            )],
            enabled=True,
            is_ipv6_enabled=True,
            comment=None,
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
                "Environment": self.long_env_tag,
            },
            viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
                cloudfront_default_certificate=True,
            )
        )
        self.url = self.cloudfront_distribution.domain_name
        self.register_outputs(
            dict(
                bucket_name=self.bucket.id,
                s3_url=self.bucket.website_endpoint,
                url=self.url
            )
        )
