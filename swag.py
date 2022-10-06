from typing import Any, Optional

import pulumi
import requests as requests
from pulumi import ResourceOptions
from pulumi.dynamic import CreateResult

SUBMISSION_URL = "https://hooks.airtable.com/workflows/v1/genericWebhook/apptZjyaJx5J2BVri/wflmg3riOP6fPjCII/wtr3RoDcz3mTizw3C"


class SwagProvider(pulumi.dynamic.ResourceProvider):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def create(self, props: Any) -> CreateResult:
        print('Sending a POST request for the Swag')
        request = requests.post(
            SUBMISSION_URL,
            json=props
        )
        print (request.status_code)
        assert request.status_code == 200
        return CreateResult(
            props['email'],
            outs=props
        )


class Swag(pulumi.dynamic.Resource):
    def __init__(self, name: str, props,
                 opts: Optional[ResourceOptions] = None) -> None:
        super().__init__(SwagProvider(name), name, props, opts)
