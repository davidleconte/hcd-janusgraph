#!/bin/bash
# TLS/SSL Certificate Generation Script
# Generates self-signed certificates for all services
# File: scripts/security/generate_certificates.sh
# Created: 2026-01-28
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CERT_DIR="$PROJECT_ROOT/config/certs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔐 TLS/SSL Certificate Generation"
echo "=================================="
echo ""

# Create certificate directory
mkdir -p "$CERT_DIR"/{ca,janusgraph,hcd,opensearch,grafana}

# Certificate validity (days)
VALIDITY_DAYS=365

# Organization details
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="HCD JanusGraph Stack"
OU="Security Team"

echo "📁 Certificate directory: $CERT_DIR"
echo "⏰ Validity: $VALIDITY_DAYS days"
echo ""

# Function to generate CA certificate
generate_ca() {
    echo "1️⃣  Generating Root Certificate Authority (CA)..."

    # Generate CA private key
    openssl genrsa -out "$CERT_DIR/ca/ca-key.pem" 4096

    # Generate CA certificate
    openssl req -new -x509 -days $VALIDITY_DAYS \
        -key "$CERT_DIR/ca/ca-key.pem" \
        -out "$CERT_DIR/ca/ca-cert.pem" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=Root CA"

    echo -e "${GREEN}✅ Root CA generated${NC}"
    echo ""
}

# Function to generate service certificate
generate_service_cert() {
    local service=$1
    local cn=$2
    local san=$3

    echo "🔧 Generating certificate for $service..."

    local service_dir="$CERT_DIR/$service"

    # Generate private key
    openssl genrsa -out "$service_dir/${service}-key.pem" 2048

    # Create certificate signing request (CSR)
    openssl req -new \
        -key "$service_dir/${service}-key.pem" \
        -out "$service_dir/${service}.csr" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$OU/CN=$cn"

    # Create SAN configuration
    cat > "$service_dir/${service}-san.cnf" <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORG
OU = $OU
CN = $cn

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
$san
EOF

    # Sign certificate with CA
    openssl x509 -req -days $VALIDITY_DAYS \
        -in "$service_dir/${service}.csr" \
        -CA "$CERT_DIR/ca/ca-cert.pem" \
        -CAkey "$CERT_DIR/ca/ca-key.pem" \
        -CAcreateserial \
        -out "$service_dir/${service}-cert.pem" \
        -extensions v3_req \
        -extfile "$service_dir/${service}-san.cnf"

    # Create full chain certificate
    cat "$service_dir/${service}-cert.pem" "$CERT_DIR/ca/ca-cert.pem" \
        > "$service_dir/${service}-fullchain.pem"

    # Set proper permissions
    chmod 600 "$service_dir/${service}-key.pem"
    chmod 644 "$service_dir/${service}-cert.pem"

    echo -e "${GREEN}✅ Certificate generated for $service${NC}"
    echo ""
}

# Function to create Java keystore (for JanusGraph/HCD)
create_java_keystore() {
    local service=$1
    local password=$2

    echo "☕ Creating Java keystore for $service..."

    local service_dir="$CERT_DIR/$service"

    # Convert PEM to PKCS12
    openssl pkcs12 -export \
        -in "$service_dir/${service}-cert.pem" \
        -inkey "$service_dir/${service}-key.pem" \
        -out "$service_dir/${service}.p12" \
        -name "$service" \
        -CAfile "$CERT_DIR/ca/ca-cert.pem" \
        -caname "root" \
        -password "pass:$password"

    # Convert PKCS12 to JKS
    keytool -importkeystore \
        -deststorepass "$password" \
        -destkeypass "$password" \
        -destkeystore "$service_dir/${service}-keystore.jks" \
        -srckeystore "$service_dir/${service}.p12" \
        -srcstoretype PKCS12 \
        -srcstorepass "$password" \
        -alias "$service" \
        -noprompt

    # Import CA certificate into truststore
    keytool -import \
        -trustcacerts \
        -alias "root-ca" \
        -file "$CERT_DIR/ca/ca-cert.pem" \
        -keystore "$service_dir/${service}-truststore.jks" \
        -storepass "$password" \
        -noprompt

    echo -e "${GREEN}✅ Java keystore created for $service${NC}"
    echo ""
}

# Main execution
main() {
    echo "Starting certificate generation..."
    echo ""

    # Generate Root CA
    generate_ca

    # Generate JanusGraph certificates
    echo "2️⃣  Generating JanusGraph certificates..."
    generate_service_cert "janusgraph" "janusgraph-server" \
        "DNS.1 = janusgraph-server\nDNS.2 = janusgraph\nDNS.3 = localhost\nIP.1 = 127.0.0.1"

    # Get keystore password from environment or use default
    KEYSTORE_PASSWORD="${SSL_KEYSTORE_PASSWORD:-changeit}"
    create_java_keystore "janusgraph" "$KEYSTORE_PASSWORD"

    # Generate HCD certificates
    echo "3️⃣  Generating HCD certificates..."
    generate_service_cert "hcd" "hcd-server" \
        "DNS.1 = hcd-server\nDNS.2 = hcd\nDNS.3 = localhost\nIP.1 = 127.0.0.1"
    create_java_keystore "hcd" "$KEYSTORE_PASSWORD"

    # Generate OpenSearch certificates
    echo "4️⃣  Generating OpenSearch certificates..."
    generate_service_cert "opensearch" "opensearch" \
        "DNS.1 = opensearch\nDNS.2 = opensearch-node1\nDNS.3 = localhost\nIP.1 = 127.0.0.1"

    # Generate Grafana certificates
    echo "5️⃣  Generating Grafana certificates..."
    generate_service_cert "grafana" "grafana" \
        "DNS.1 = grafana\nDNS.2 = localhost\nIP.1 = 127.0.0.1"

    # Create combined certificate bundle
    echo "6️⃣  Creating certificate bundle..."
    cat "$CERT_DIR"/*/*.pem > "$CERT_DIR/all-certs-bundle.pem" 2>/dev/null || true

    # Generate certificate information file
    cat > "$CERT_DIR/README.md" <<EOF
# TLS/SSL Certificates

Generated: $(date)
Validity: $VALIDITY_DAYS days
Expires: $(date -d "+$VALIDITY_DAYS days" 2>/dev/null || date -v +${VALIDITY_DAYS}d)

## Certificate Structure

\`\`\`
$CERT_DIR/
├── ca/
│   ├── ca-key.pem          # Root CA private key (KEEP SECURE!)
│   └── ca-cert.pem         # Root CA certificate
├── janusgraph/
│   ├── janusgraph-key.pem  # Private key
│   ├── janusgraph-cert.pem # Certificate
│   ├── janusgraph-keystore.jks   # Java keystore
│   └── janusgraph-truststore.jks # Java truststore
├── hcd/
│   ├── hcd-key.pem         # Private key
│   ├── hcd-cert.pem        # Certificate
│   ├── hcd-keystore.jks    # Java keystore
│   └── hcd-truststore.jks  # Java truststore
├── opensearch/
│   ├── opensearch-key.pem  # Private key
│   └── opensearch-cert.pem # Certificate
└── grafana/
    ├── grafana-key.pem     # Private key
    └── grafana-cert.pem    # Certificate
\`\`\`

## Usage

### JanusGraph
Mount keystore and truststore in container:
\`\`\`yaml
volumes:
  - ./config/certs/janusgraph:/etc/opt/janusgraph/certs:ro
\`\`\`

### HCD
Configure in cassandra.yaml:
\`\`\`yaml
client_encryption_options:
  enabled: true
  keystore: /etc/hcd/certs/hcd-keystore.jks
  keystore_password: \${KEYSTORE_PASSWORD}
\`\`\`

### OpenSearch
Mount certificates:
\`\`\`yaml
volumes:
  - ./config/certs/opensearch:/usr/share/opensearch/config/certs:ro
\`\`\`

## Security Notes

1. **NEVER** commit certificates to version control
2. **KEEP** ca-key.pem secure (root CA private key)
3. **ROTATE** certificates before expiration
4. **USE** strong keystore passwords
5. **BACKUP** certificates securely

## Certificate Renewal

To renew certificates before expiration:
\`\`\`bash
./scripts/security/generate_certificates.sh
\`\`\`

Then restart all services to load new certificates.
EOF

    # Set proper permissions
    chmod 700 "$CERT_DIR/ca"
    chmod 600 "$CERT_DIR/ca/ca-key.pem"

    # Summary
    echo ""
    echo "=================================="
    echo -e "${GREEN}✅ Certificate Generation Complete${NC}"
    echo "=================================="
    echo ""
    echo "📁 Certificates location: $CERT_DIR"
    echo "📄 Documentation: $CERT_DIR/README.md"
    echo ""
    echo "⚠️  IMPORTANT SECURITY NOTES:"
    echo "   1. Keep ca-key.pem secure (root CA private key)"
    echo "   2. Never commit certificates to version control"
    echo "   3. Certificates expire in $VALIDITY_DAYS days"
    echo "   4. Update .gitignore to exclude $CERT_DIR"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Update docker-compose files to mount certificates"
    echo "   2. Configure services to use TLS/SSL"
    echo "   3. Update client connections to use HTTPS/TLS"
    echo "   4. Test encrypted connections"
    echo ""

    # Add to .gitignore
    if ! grep -q "config/certs" "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
        echo "config/certs/" >> "$PROJECT_ROOT/.gitignore"
        echo -e "${GREEN}✅ Added config/certs/ to .gitignore${NC}"
    fi
}

# Run main function
main

echo "Certificate generation script completed successfully!"

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
