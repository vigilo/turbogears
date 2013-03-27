# -*- coding: utf-8 -*-
"""
Repris de TurboGears 2.2.2.
Assure l'indépendance vis-à-vis de Routes et de ses bugs bizarres.

Copright Mark Ramm, Christopher Perkins, Jonathan LaCour, Rick Copland,
         Alberto Valverde, Michael Pedersen, Alessandro Molina,
         and the TurboGears community
"""
import urllib
import pylons

def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.

    This function was borrowed from Django.

    """
    if strings_only and (s is None or isinstance(s, int)):
        return s
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        r = s.encode(encoding, errors)
        return r
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s


def generate_smart_str(params):
    for key, value in params.iteritems():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                yield smart_str(key), smart_str(item)
        else:
            yield smart_str(key), smart_str(value)


def urlencode(params):
    """
    A version of Python's urllib.urlencode() function that can operate on
    unicode strings. The parameters are first case to UTF-8 encoded strings and
    then encoded as per normal.
    """
    return urllib.urlencode([i for i in generate_smart_str(params)])


def url(base_url='/', params={}, qualified=False):
    """Generate an absolute URL that's specific to this application.

    The URL function takes a string (base_url) and, appends the
    SCRIPT_NAME and adds parameters for all of the
    parameters passed into the params dict.

    """
    if not isinstance(base_url, basestring) and hasattr(base_url, '__iter__'):
        base_url = '/'.join(base_url)

    if base_url.startswith('/'):
        base_url = pylons.request.environ['SCRIPT_NAME'] + base_url
        if qualified:
            base_url = pylons.request.host_url + base_url

    if params:
        return '?'.join((base_url, urlencode(params)))

    return base_url


def patch_tg_url():
    """Monkey-patch tg.url() to avoid Routes' quirks."""
    import tg
    from tg import controllers
    tg.url = url # utilisé par les templates
    controllers.url = url # utilisé par le code Python
