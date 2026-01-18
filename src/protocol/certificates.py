"""
Certificate Generation Module.
Generates self-signed TLS 1.3 certificates for QUIC.
"""
import datetime
import os
import logging
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from config import cfg

logger = logging.getLogger("CertMgr")

class CertificateManager:
    @staticmethod
    def ensure_certs():
        """
        Check if certs exist, otherwise generate them.
        """
        if os.path.exists(cfg.CERT_PATH) and os.path.exists(cfg.KEY_PATH):
            logger.info("Certificates found.")
            return

        logger.info("Generating new self-signed certificates...")
        os.makedirs(os.path.dirname(cfg.CERT_PATH), exist_ok=True)

        # Generate Private Key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate Certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Denial"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Nowhere"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Hampter Corp"),
            x509.NameAttribute(NameOID.COMMON_NAME, cfg.get_hostname()),
        ])
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            subject
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            now + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(cfg.get_hostname())]),
            critical=False,
        ).sign(key, hashes.SHA256())

        # Save Private Key
        with open(cfg.KEY_PATH, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        # Save Certificate
        with open(cfg.CERT_PATH, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        logger.info(f"Certificates generated at {cfg.CERT_DIR}")
