import os
import ssl


if 'SSL_CERT_FILE' not in os.environ and 'SSL_CERT_DIR' not in os.environ:
	paths = ssl.get_default_verify_paths()
	if paths.cafile is None and paths.capath is None:
		for certificate_file in (
			'/etc/ssl/certs/ca-certificates.crt',
			'/etc/pki/tls/certs/ca-bundle.crt',
			'/etc/ssl/cert.pem',
		):
			if os.path.isfile(certificate_file):
				os.environ['SSL_CERT_FILE'] = certificate_file
				break
