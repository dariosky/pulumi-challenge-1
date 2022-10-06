"""An AWS Python Pulumi program"""
import os

import pulumi

from cdn_website import CDNWebsite
from swag import Swag

name = os.environ.get('PULUMI_SWAG_NAME')
email = os.environ.get('PULUMI_SWAG_EMAIL')
address = os.environ.get('PULUMI_SWAG_ADDRESS')
size = os.environ.get('PULUMI_SWAG_SIZE')

site = CDNWebsite('pulumi-challenge-1')
swag = Swag(f'{name} Swag',
            {
                'name': name,
                'email': email,
                'address': address,
                'size': size,
            }
            )
pulumi.export('readme', 'A stack to play with Pulumi - and solve the challenge #1')
pulumi.export('site', site.url)
