import logging
import json
from http import HTTPStatus

from api.helpers import CONFIG_TABLE_NAME
from api.helpers import dynamodb_r
from api.helpers import http_response
from api.helpers import _get_body

log = logging.getLogger()
log.setLevel(logging.INFO)

config_table = dynamodb_r.Table(CONFIG_TABLE_NAME)

############################
######  Helpers  ###########
############################

def get_all_sites() -> list:
    """Helper to retrieve a list of all existing sitecodes."""

    config_entries = config_table.scan()['Items']
    return [ entry['site'] for entry in config_entries ]


def get_site_config(site: str) -> dict:
    """Helper to retrieve the config details for a given site.

    Renamed off get_config: the handler below had the same name and, being
    defined second, replaced this one entirely. Nothing could reach it, and
    anything that tried would have called the handler with a sitecode where it
    expected an API Gateway event. Returns None when the site has no config,
    rather than raising KeyError at the caller.
    """

    result = config_table.get_item(Key = { "site": site })
    return result.get('Item')


############################
######  Handlers ###########
############################

def get_config(event, context):
    """Retrieves the config file details from a specified site.
    
    Args:
        event.body.site (str): Sitecode to retrieve config from (eg. "saf").

    Returns:
        200 status code with site config file.
    """

    site = event['pathParameters']['site']
    config = config_table.get_item(Key = { "site": site })
    # get_item returns a response with no 'Item' when the key is not there, so
    # subscripting it raised KeyError and an unknown sitecode came back as a
    # 500. A site that does not exist is a perfectly ordinary request to make.
    if 'Item' not in config:
        return http_response(HTTPStatus.NOT_FOUND, f"No config exists for site {site}")
    return http_response(HTTPStatus.OK, config['Item'])


# TODO: add config file key-values validation
def put_config(event, context):
    """Adds a new config file to a specified site.

    Args:
        event.body.site (str): Sitecode to retrieve config from (eg. "saf").

    Returns:
        200 status code with site config file successfully added.
    """

    site = event['pathParameters']['site']
    body = _get_body(event)
    response = config_table.put_item(Item = {
        "site": site,
        "configuration": body
    })
    return http_response(HTTPStatus.OK, response)


def delete_config(event, context):
    """Deletes the config details for a specified site.

    Args:
        event.body.site (str): Sitecode to delete config from (eg. "saf").

    Returns:
        200 status code with site config file.
    """
    
    site = event['pathParameters']['site']
    response = config_table.delete_item(Key={"site": site})
    return http_response(HTTPStatus.OK, response)


def all_config(event, context):
    """Retrieves a list of all site configs.
    
    Returns:
        200 status code with all site configs.
    """
    
    response = config_table.scan()
    items = {}
    for entry in response['Items']: 
        items[entry['site']] = entry['configuration']
    return http_response(HTTPStatus.OK, items)

