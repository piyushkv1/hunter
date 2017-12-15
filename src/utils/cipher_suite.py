from socket import socket
from ssl import SSLContext
from ssl import PROTOCOL_SSLv23
from ssl import DER_cert_to_PEM_cert

WEAK_CTX = SSLContext(PROTOCOL_SSLv23)
WEAK_CTX.set_ciphers('ALL:!aNULL:!eNULL')

NORMAL_CTX = SSLContext(PROTOCOL_SSLv23)
NORMAL_CTX.set_ciphers(
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)
NORMAL_CTX.set_ciphers(
    'DEFAULT:!aNULL:!eNULL:!LOW:!EXPORT:!SSLv3'
)


def getCertificate(addr):
    sock = socket()
    sock.connect(addr)
    isWeakCipher = False
    try:
        sslobj = NORMAL_CTX._wrap_socket(sock._sock, server_side=False)
        sslobj.do_handshake()
    except Exception as ex:
        if hasattr(ex, 'reason') and ex.reason == 'SSLV3_ALERT_HANDSHAKE_FAILURE':
            sock.close()
            sock = socket()
            sock.connect(addr)
            sslobj = WEAK_CTX._wrap_socket(sock._sock, server_side=False)
            sslobj.do_handshake()
            isWeakCipher = True
        else:
            raise
    cipher = sslobj.cipher()

    cert = sslobj.peer_certificate(True)
    sock.close()
    return isWeakCipher, cipher, cert

if __name__ == '__main__':
    print getCertificate(("10.144.137.94", 443))
