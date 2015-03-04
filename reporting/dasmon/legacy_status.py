import httplib
import json
import logging
import sys
from dasmon.models import LegacyURL

STATUS_HOST = 'neutrons.ornl.gov'
def get_ops_status(instrument_id):
    """
        Pull the legacy status information
    """
    try:
        conn = httplib.HTTPConnection(STATUS_HOST, timeout=0.5)
        url = get_legacy_url(instrument_id, False)
        conn.request('GET', '%s/data.json' % url)
        r = conn.getresponse()
        data = json.loads(r.read())
        organized_data = []
        groups = data.keys()
        groups.sort()
        for group in groups:
            key_value_pairs = []
            keys = data[group].keys()
            keys.sort()
            for item in keys:
                key_value_pairs.append({'key':item.replace(' ', '_').replace('(%)','[pct]').replace('(', '[').replace(')', ']').replace('#',''),
                                        'value': data[group][item]})
            organized_data.append({'group':group,
                                   'data':key_value_pairs})
        return organized_data
    except:
        logging.warning("Could not get legacy DAS status: %s" % sys.exc_value)
        return []

def get_legacy_url(instrument_id, include_domain=True):
    try:
        url_obj = LegacyURL.objects.get(instrument_id=instrument_id)
        url = url_obj.url
    except:
        url = '/%s/status/' % instrument_id.name
        
    if include_domain:
        url = 'http://%s%s' % (STATUS_HOST, url)
    return url
    