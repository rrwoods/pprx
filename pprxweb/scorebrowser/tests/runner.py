from contextlib import contextmanager
import ipaddress
import os
import socket
from django.test.runner import DiscoverRunner


PROXY_ENV_VARS = (
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
)


class NetworkBlockedError(RuntimeError):
    def __init__(self, message="Network access blocked during tests"):
        super().__init__(message)


def _is_local_host(host):
    if host in ('localhost', None, ''):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_local_address(address):
    if isinstance(address, (str, bytes)):
        return True
    if isinstance(address, tuple) and len(address) >= 2:
        host = address[0]
        return _is_local_host(host)
    return False


@contextmanager
def block_network():
    saved_env = {var: os.environ[var] for var in PROXY_ENV_VARS if var in os.environ}
    for var in PROXY_ENV_VARS:
        os.environ.pop(var, None)

    orig_connect = socket.socket.connect
    orig_connect_ex = socket.socket.connect_ex
    orig_sendto = socket.socket.sendto
    orig_getaddrinfo = socket.getaddrinfo
    orig_gethostbyname = socket.gethostbyname
    orig_gethostbyname_ex = socket.gethostbyname_ex
    orig_gethostbyaddr = socket.gethostbyaddr
    orig_getnameinfo = socket.getnameinfo
    orig_getfqdn = socket.getfqdn

    def blocked_connect(self, address):
        if not _is_local_address(address):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_connect(self, address)

    def blocked_connect_ex(self, address):
        if not _is_local_address(address):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_connect_ex(self, address)

    def blocked_sendto(self, data, *args):
        address = args[-1] if args else None
        if address is not None and not _is_local_address(address):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_sendto(self, data, *args)

    def blocked_getaddrinfo(host, port, *args, **kwargs):
        if not _is_local_host(host):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_getaddrinfo(host, port, *args, **kwargs)

    def blocked_gethostbyname(hostname):
        if not _is_local_host(hostname):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_gethostbyname(hostname)

    def blocked_gethostbyname_ex(hostname):
        if not _is_local_host(hostname):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_gethostbyname_ex(hostname)

    def blocked_gethostbyaddr(ip_address):
        if not _is_local_host(ip_address):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_gethostbyaddr(ip_address)

    def blocked_getnameinfo(sockaddr, flags):
        host = sockaddr[0] if isinstance(sockaddr, tuple) and sockaddr else None
        if not _is_local_host(host):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_getnameinfo(sockaddr, flags)

    def blocked_getfqdn(name=''):
        name = (name or '').strip()
        if not name or name == 'localhost':
            return 'localhost'
        if not _is_local_host(name):
            raise NetworkBlockedError("Network access blocked during tests")
        return orig_getfqdn(name)

    socket.socket.connect = blocked_connect
    socket.socket.connect_ex = blocked_connect_ex
    socket.socket.sendto = blocked_sendto
    socket.getaddrinfo = blocked_getaddrinfo
    socket.gethostbyname = blocked_gethostbyname
    socket.gethostbyname_ex = blocked_gethostbyname_ex
    socket.gethostbyaddr = blocked_gethostbyaddr
    socket.getnameinfo = blocked_getnameinfo
    socket.getfqdn = blocked_getfqdn
    try:
        yield
    finally:
        socket.socket.connect = orig_connect
        socket.socket.connect_ex = orig_connect_ex
        socket.socket.sendto = orig_sendto
        socket.getaddrinfo = orig_getaddrinfo
        socket.gethostbyname = orig_gethostbyname
        socket.gethostbyname_ex = orig_gethostbyname_ex
        socket.gethostbyaddr = orig_gethostbyaddr
        socket.getnameinfo = orig_getnameinfo
        socket.getfqdn = orig_getfqdn
        for var in PROXY_ENV_VARS:
            if var in saved_env:
                os.environ[var] = saved_env[var]
            else:
                os.environ.pop(var, None)


class PPRXTestRunner(DiscoverRunner):
    def check_database_engines(self):
        from django.conf import settings
        for alias, config in settings.DATABASES.items():
            engine = config.get("ENGINE", "")
            if not engine.endswith("sqlite3"):
                raise RuntimeError(
                    f"Database engine '{engine}' for database '{alias}' is not allowed during tests; only SQLite is supported."
                )

    def setup_databases(self, **kwargs):
        self.check_database_engines()
        return super().setup_databases(**kwargs)

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        with block_network():
            return super().run_tests(test_labels, extra_tests=extra_tests, **kwargs)
