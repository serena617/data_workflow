# Local application settings for monitoring web application
from django_auth_ldap.config import LDAPSearch, PosixGroupType
import ldap 
DEBUG = True

"""
    Authentication settings
"""
AUTH_LDAP_SERVER_URI = "ldaps://data.sns.gov/"
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_DN_TEMPLATE = 'uid=%(user)s,ou=Users,dc=sns,dc=ornl,dc=gov'
AUTH_LDAP_GROUP_SEARCH = "LDAPSearch( 'ou=Groups,dc=sns,dc=ornl,dc=gov', ldap.SCOPE_SUBTREE, '(objectClass=posixGroup)')"

AUTH_LDAP_GROUP_TYPE = PosixGroupType()

AUTH_LDAP_ALWAYS_UPDATE_USER = True

ALLOW_GUESTS = True
GRAVATAR_URL = "http://www.gravatar.com/avatar/"
#ALLOWED_DOMAIN = 'ornl.gov'
ALLOWED_DOMAIN = ''

"""
    ICAT server settings
"""
ICAT_DOMAIN = 'icat-testing.sns.gov'
ICAT_PORT = 2080

"""
    Dev settings: do not copy to production
"""
INTERNAL_IPS = ('127.0.0.1', 'localhost',)

