import os
from collections import namedtuple

from six.moves.configparser import ConfigParser, NoSectionError, NoOptionError


Profile = namedtuple(
    'Profile',
    ['domain', 'protocol', 'client_id', 'client_secret']
)

DEFAULT_PROFILE = 'default'
DEFAULT_DOMAIN = 'sherlockml.com'
DEFAULT_PROTOCOL = 'https'


def load(path):
    """Read the SherlockML configuration from a file."""

    parser = ConfigParser()
    parser.read(str(path))

    def _get(section, option):
        try:
            return parser.get(section, option)
        except (NoSectionError, NoOptionError):
            return None

    profiles = {}

    for section in parser.sections():
        profiles[section] = Profile(
            domain=_get(section, 'domain'),
            protocol=_get(section, 'protocol'),
            client_id=_get(section, 'client_id'),
            client_secret=_get(section, 'client_secret')
        )

    return profiles


def load_profile(path, profile):
    """Read a SherlockML profile from a file."""
    profiles = load(path)
    try:
        return profiles[profile]
    except KeyError:
        return Profile(None, None, None, None)


def _default_configuration_path():
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if not xdg_config_home:
        xdg_config_home = os.path.expanduser('~/.config')
    return os.path.join(xdg_config_home, 'sherlockml', 'configuration')


class CredentialsError(RuntimeError):
    pass


def _missing_credentials(type_):
    raise CredentialsError('No {} found'.format(type_))


def resolve_profile(configuration_path=None, profile_name=None, domain=None,
                    protocol=None, client_id=None, client_secret=None):

    resolved_configuration_path = (
        configuration_path
        or os.getenv('SHERLOCKML_CONFIGURATION')
        or _default_configuration_path()
    )

    resolved_profile_name = (
        profile_name
        or os.getenv('SHERLOCKML_PROFILE')
        or DEFAULT_PROFILE
    )

    profile = load_profile(resolved_configuration_path, resolved_profile_name)

    resolved_domain = (
        domain
        or os.getenv('SHERLOCKML_DOMAIN')
        or profile.domain
        or DEFAULT_DOMAIN
    )

    resolved_protocol = (
        protocol
        or os.getenv('SHERLOCKML_PROTOCOL')
        or profile.protocol
        or DEFAULT_PROTOCOL
    )

    resolved_client_id = (
        client_id
        or os.getenv('SHERLOCKML_CLIENT_ID')
        or profile.client_id
        or _missing_credentials('client_id')
    )

    resolved_client_secret = (
        client_secret
        or os.getenv('SHERLOCKML_CLIENT_SECRET')
        or profile.client_secret
        or _missing_credentials('client_secret')
    )

    return Profile(
        domain=resolved_domain,
        protocol=resolved_protocol,
        client_id=resolved_client_id,
        client_secret=resolved_client_secret
    )
