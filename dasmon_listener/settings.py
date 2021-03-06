# Django settings for reporting_app project.
import os
import django

# The DB settings are defined in the workflow manager
from workflow.database.settings import DATABASES
DATABASES['default']['CONN_MAX_AGE']=25

SECRET_KEY = '-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn'

TIME_ZONE = 'America/New_York'

USE_TZ = True

INSTALLED_APPS = (
    'report',
    'dasmon',
    )

"""
    ActiveMQ settings
"""
# List of brokers
from workflow.database.settings import brokers
from workflow.database.settings import icat_user as amq_user
from workflow.database.settings import icat_passcode as amq_pwd

queues = ["/topic/ADARA.APP.DASMON.0",
          "/topic/ADARA.STATUS.DASMON.0",
          "/topic/ADARA.SIGNAL.DASMON.0"]

INSTALLATION_DIR = "/var/www/workflow/app"

PURGE_TIMEOUT = 7

LEGACY_PREFIX = "ADARA"
LEGACY_INSTRUMENT = "hysa"
TOPIC_PREFIX = "SNS"

# Import local settings if available
try:
    from local_settings import *
except ImportError, e:
    LOCAL_SETTINGS = False
    pass
   
