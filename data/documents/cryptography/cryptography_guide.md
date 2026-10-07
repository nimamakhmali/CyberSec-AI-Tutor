# Cryptography Guide

## Symmetric Encryption

### AES (Advanced Encryption Standard)
Block cipher with 128-bit block size, key sizes: 128, 192, 256 bits.

#### Modes of Operation
- **ECB (Electronic Codebook)**: Deterministic, **NOT SECURE** for multiple blocks
- **CBC (Cipher Block Chaining)**: Requires IV, sequential encryption
- **CTR (Counter)**: Turns block cipher into stream cipher, parallelizable
- **GCM (Galois/Counter Mode)**: Authenticated encryption (AEAD), **RECOMMENDED**
- **CCM (Counter with CBC-MAC)**: AEAD, used in TLS 1.2

#### AES-GCM Example (Python)
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = os.urandom(32)  # 256-bit key
aesgcm = AESGCM(key)
nonce = os.urandom(12)  # 96-bit nonce (recommended for GCM)
plaintext = b"Secret message"
associated_data = b"header"

ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
decrypted = aesgcm.decrypt(nonce, ciphertext, associated_data)
```

### ChaCha20-Poly1305
Stream cipher + MAC, alternative to AES-GCM, faster on non-AES-NI CPUs.

## Asymmetric Encryption

### RSA
Based on integer factorization difficulty.

#### Key Sizes
- **2048 bits**: Minimum recommended (deprecated for new systems)
- **3072 bits**: Recommended for new systems
- **4096 bits**: High security, longer-term

#### RSA Padding
- **PKCS#1 v1.5**: Legacy, vulnerable to Bleichenbacher attacks
- **OAEP (Optimal Asymmetric Encryption Padding)**: **RECOMMENDED**

### ECC (Elliptic Curve Cryptography)
Smaller keys, equivalent security to larger RSA keys.

#### Common Curves
- **P-256 (secp256r1)**: NIST standard, ~128-bit security
- **P-384 (secp384r1)**: ~192-bit security
- **P-521 (secp521r1)**: ~256-bit security
- **Curve25519**: Modern, fast, ~128-bit security (used in X25519, Ed25519)
- **secp256k1**: Bitcoin/Ethereum curve

#### ECC Key Size Comparison
| ECC Curve | RSA Equivalent | Security Level |
|-----------|----------------|----------------|
| P-256     | 3072-bit       | 128-bit        |
| P-384     | 7680-bit       | 192-bit        |
| P-521     | 15360-bit      | 256-bit        |

## Hash Functions

### SHA-2 Family
- **SHA-224**: 224-bit output
- **SHA-256**: 256-bit output, widely used
- **SHA-384**: 384-bit output
- **SHA-512**: 512-bit output
- **SHA-512/224**, **SHA-512/256**: Truncated variants

### SHA-3 Family (Keccak)
- **SHA3-224**, **SHA3-256**, **SHA3-384**, **SHA3-512**
- Different internal structure from SHA-2
- **SHAKE128**, **SHAKE256**: Extendable Output Functions (XOF)

### BLAKE2 / BLAKE3
- Faster than SHA-2/3, similar security
- BLAKE3: Highly parallelizable, based on Bao tree hashing

### Password Hashing (Key Derivation)
**NEVER use general-purpose hashes for passwords!**

- **Argon2**: **RECOMMENDED** (Argon2id default)
- **scrypt**: Memory-hard, older alternative
- **bcrypt**: Older, still acceptable with high cost
- **PBKDF2**: Legacy, requires high iteration count

```python
# Argon2 example
from argon2 import PasswordHasher

ph = PasswordHasher()
hash = ph.hash("password123")
ph.verify(hash, "password123")  # Raises exception if invalid
```

## Digital Signatures

### RSA Signatures
- **RSA-PSS (Probabilistic Signature Scheme)**: **RECOMMENDED**
- **PKCS#1 v1.5**: Legacy

### ECDSA (Elliptic Curve DSA)
Used with P-256, P-384, P-521 curves.

### EdDSA (Edwards-curve DSA)
- **Ed25519**: Curve25519, fast, deterministic, **RECOMMENDED**
- **Ed448**: Higher security level

## Key Exchange

### Diffie-Hellman (DH)
Classic key exchange, requires safe prime groups.

### ECDH (Elliptic Curve DH)
Elliptic curve variant, smaller keys.

#### Common Key Exchange Protocols
- **X25519**: Curve25519 ECDH, used in TLS 1.3, Signal, WireGuard
- **X448**: Curve448 ECDH, higher security

### TLS Key Exchange
- **TLS 1.2**: RSA, DH, ECDH key exchange
- **TLS 1.3**: Only (EC)DHE with forward secrecy

## TLS / SSL

### TLS 1.3 (RFC 8446) - **RECOMMENDED**
- Only AEAD ciphers (AES-GCM, ChaCha20-Poly1305)
- Only (EC)DHE key exchange (forward secrecy mandatory)
- 0-RTT resumption (with replay risk)
- Encrypted SNI (ESNI/ECH)

### Cipher Suites (TLS 1.3)
```
TLS_AES_256_GCM_SHA384
TLS_CHACHA20_POLY1305_SHA256
TLS_AES_128_GCM_SHA256
```

### Certificate Types
- **DV (Domain Validated)**: Basic domain control verification
- **OV (Organization Validated)**: Organization identity verified
- **EV (Extended Validated)**: Strict verification, green bar (deprecated in browsers)

### Certificate Transparency
Public logs of all issued certificates for accountability.

## PKI (Public Key Infrastructure)

### Certificate Chain
```
Root CA (self-signed)
  └── Intermediate CA
        └── Leaf Certificate (your domain)
```

### Certificate Formats
- **PEM**: Base64 encoded DER, `-----BEGIN CERTIFICATE-----`
- **DER**: Binary encoding
- **PKCS#7 / P7B**: Certificate chain
- **PKCS#12 / PFX**: Certificate + private key (password protected)

### OCSP (Online Certificate Status Protocol)
Real-time certificate revocation checking.

### CRL (Certificate Revocation List)
Periodically published list of revoked certificates.

## Common Protocols Using Cryptography

### SSH (Secure Shell)
- Key exchange: curve25519-sha256, diffie-hellman-group-exchange-sha256
- Encryption: chacha20-poly1305, aes256-gcm, aes128-gcm
- MAC: hmac-sha2-256, hmac-sha2-512
- Authentication: publickey, keyboard-interactive

### IPsec
- AH: Authentication only
- ESP: Encryption + authentication
- IKEv2: Key exchange protocol
- Algorithms: AES-GCM, ChaCha20-Poly1305

### WireGuard
- Key exchange: X25519 (Noise protocol)
- Encryption: ChaCha20-Poly1305
- Authentication: Poly1305
- Simple, fast, formally verified

## Cryptographic Best Practices

### DO
- Use authenticated encryption (AES-GCM, ChaCha20-Poly1305)
- Use TLS 1.3 for all network communications
- Generate keys with CSPRNG (os.urandom, getrandom)
- Use constant-time comparisons for secrets
- Rotate keys regularly
- Use established libraries (libsodium, cryptography, OpenSSL)
- Implement proper key management (HSM, KMS)

### DON'T
- Roll your own crypto
- Use ECB mode
- Use MD5, SHA-1 for security purposes
- Use RSA without OAEP/PSS padding
- Use static IVs/nonces
- Hardcode keys in source code
- Use the same key for encryption and authentication
- Skip certificate validation

## Quantum-Resistant Cryptography (Post-Quantum)

### NIST PQC Standardization (2024)
- **ML-KEM (CRYSTALS-Kyber)**: Key encapsulation mechanism
- **ML-DSA (CRYSTALS-Dilithium)**: Digital signatures
- **SLH-DSA (SPHINCS+)**: Stateless hash-based signatures

### Migration Timeline
- **2024-2030**: Hybrid classical/PQ deployments
- **2030+**: Full PQC migration recommended

## Tools & Libraries

### Python
- `cryptography`: High-level, safe API
- `pycryptodome`: Lower-level, more algorithms
- `argon2-cffi`: Password hashing
- `pynacl`: libsodium bindings

### Command Line
- `openssl`: Swiss army knife
- `gpg`: PGP/GPG operations
- `ssh-keygen`: SSH keys
- `certbot`: Let's Encrypt certificates

### Testing
- `testssl.sh`: TLS configuration testing
- `sslyze`: Fast TLS scanner
- `cipherscan`: Cipher suite enumeration