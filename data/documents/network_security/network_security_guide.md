# Network Security Guide

## Network Fundamentals

### OSI Model Layers
1. **Physical**: Cables, signals, hardware
2. **Data Link**: MAC addressing, switches, frames
3. **Network**: IP addressing, routing, packets
4. **Transport**: TCP/UDP, ports, segments
5. **Session**: Connection management
6. **Presentation**: Encryption, compression
7. **Application**: HTTP, DNS, SSH, etc.

### TCP/IP Model
- **Link Layer**: Ethernet, Wi-Fi
- **Internet Layer**: IP, ICMP, ARP
- **Transport Layer**: TCP, UDP
- **Application Layer**: All application protocols

## Transport Protocols

### TCP (Transmission Control Protocol)
Connection-oriented, reliable, ordered delivery.

#### Three-Way Handshake
```
Client                    Server
  |      SYN (seq=x)       |
  |----------------------->|
  |      SYN-ACK (seq=y,   |
  |      ack=x+1)          |
  |<-----------------------|
  |      ACK (ack=y+1)     |
  |----------------------->|
  |   Connection Established
```

#### TCP Flags
- **SYN**: Synchronize sequence numbers (connection initiation)
- **ACK**: Acknowledge received data
- **FIN**: Finish (graceful connection termination)
- **RST**: Reset (immediate connection termination)
- **PSH**: Push (send data immediately)
- **URG**: Urgent pointer significant

#### TCP Connection Termination (Four-Way Handshake)
```
Client                    Server
  |      FIN (seq=u)       |
  |----------------------->|
  |      ACK (ack=u+1)     |
  |<-----------------------|
  |                        |  (Server finishes sending)
  |      FIN (seq=v)       |
  |<-----------------------|
  |      ACK (ack=v+1)     |
  |----------------------->|
  |   Connection Closed
```

### UDP (User Datagram Protocol)
Connectionless, unreliable, no ordering guarantees. Lower overhead than TCP.

Used for: DNS, DHCP, VoIP, streaming, gaming, SNMP, TFTP

## Network Scanning & Reconnaissance

### Nmap (Network Mapper)
The standard tool for network discovery and security auditing.

#### Common Scan Types
- **SYN Scan (-sS)**: Half-open scan, stealthy, default for privileged users
- **Connect Scan (-sT)**: Full TCP connection, default for non-privileged
- **UDP Scan (-sU)**: UDP port scanning, slower
- **ACK Scan (-sA)**: Firewall rule mapping
- **FIN/NULL/Xmas Scan**: Stealth scans for firewall evasion

#### Host Discovery
```bash
# Ping sweep
nmap -sn 192.168.1.0/24

# ARP scan (local network)
nmap -PR 192.168.1.0/24

# Disable host discovery
nmap -Pn 192.168.1.1
```

#### Port Scanning
```bash
# Top 1000 ports
nmap 192.168.1.1

# All ports
nmap -p- 192.168.1.1

# Specific ports
nmap -p 22,80,443 192.168.1.1

# Service version detection
nmap -sV 192.168.1.1

# OS detection
nmap -O 192.168.1.1

# Aggressive scan (OS, version, scripts, traceroute)
nmap -A 192.168.1.1
```

#### Nmap Scripting Engine (NSE)
```bash
# Default safe scripts
nmap -sC 192.168.1.1

# Specific category
nmap --script vuln 192.168.1.1

# All scripts (careful!)
nmap --script all 192.168.1.1
```

## Firewalls

### Types of Firewalls
1. **Packet Filtering**: Stateless, rule-based (ACLs)
2. **Stateful Inspection**: Tracks connection state
3. **Application Layer (Proxy)**: Deep packet inspection
4. **Next-Generation (NGFW)**: IPS, application control, SSL inspection

### iptables (Linux)
```bash
# View rules
iptables -L -n -v

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m state --state INVALID -j DROP

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
```

### nftables (Modern Linux)
```bash
# Create table
nft add table ip filter

# Create chain
nft add chain ip filter input { type filter hook input priority 0 \; policy drop \; }

# Add rule
nft add rule ip filter input tcp dport 22 accept
```

## Network Attacks

### ARP Spoofing / Poisoning
Attacker sends falsified ARP messages to link their MAC with victim's IP.

**Defense**: Dynamic ARP Inspection (DAI), static ARP entries, port security

### DNS Spoofing / Cache Poisoning
Corrupting DNS cache to redirect traffic.

**Defense**: DNSSEC, DNS over HTTPS/TLS, validating resolvers

### Man-in-the-Middle (MitM)
Intercepting and potentially modifying communications.

**Defense**: TLS/SSL, certificate pinning, HSTS, VPN

### SYN Flood (DoS)
Overwhelming server with SYN packets without completing handshake.

**Defense**: SYN cookies, rate limiting, firewalls with DDoS protection

### IP Spoofing
Forging source IP address in packets.

**Defense**: Ingress/egress filtering (BCP 38), uRPF

## Network Security Monitoring

### Zeek (formerly Bro)
Network analysis framework for traffic analysis.

### Suricata
High-performance IDS/IPS/NSM engine.

### Snort
Classic rule-based IDS/IPS.

### Wireshark
Packet capture and analysis GUI tool.

## VPN Technologies

### IPsec
- **AH (Authentication Header)**: Integrity/authentication
- **ESP (Encapsulating Security Payload)**: Encryption + integrity
- **Modes**: Transport (end-to-end) vs Tunnel (gateway-to-gateway)

### WireGuard
Modern, lightweight VPN protocol with formal verification.

### OpenVPN
SSL/TLS-based VPN, highly configurable.

### Zero Trust Network Access (ZTNA)
Identity-based access, no implicit trust based on network location.

## Wireless Security

### WPA3
Latest Wi-Fi security protocol with:
- SAE (Simultaneous Authentication of Equals) - replaces PSK
- Forward secrecy
- 192-bit encryption (Enterprise)

### Common Attacks
- **WPA2 KRACK**: Key reinstallation attack
- **WPS PIN Brute Force**: Offline PIN guessing
- **Evil Twin**: Rogue access point
- **Deauthentication**: Forcing reconnection to capture handshake

## Network Segmentation

### VLANs (Virtual LANs)
Logical separation of broadcast domains.

### DMZ (Demilitarized Zone)
Isolated network segment for public-facing services.

### Micro-segmentation
Workload-level segmentation using software-defined networking.

### Zero Trust Architecture
- **Never trust, always verify**
- Least privilege access
- Continuous verification
- Assume breach mentality

## Common Ports Reference

| Port | Protocol | Service |
|------|----------|---------|
| 20/21 | TCP | FTP |
| 22 | TCP | SSH |
| 23 | TCP | Telnet (insecure) |
| 25 | TCP | SMTP |
| 53 | TCP/UDP | DNS |
| 67/68 | UDP | DHCP |
| 69 | UDP | TFTP |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 |
| 123 | UDP | NTP |
| 135 | TCP | RPC |
| 139/445 | TCP | SMB/NetBIOS |
| 143 | TCP | IMAP |
| 161/162 | UDP | SNMP |
| 389 | TCP | LDAP |
| 443 | TCP | HTTPS |
| 445 | TCP | SMB |
| 465 | TCP | SMTPS |
| 587 | TCP | SMTP (submission) |
| 636 | TCP | LDAPS |
| 993 | TCP | IMAPS |
| 995 | TCP | POP3S |
| 1433 | TCP | MSSQL |
| 3306 | TCP | MySQL |
| 3389 | TCP | RDP |
| 5432 | TCP | PostgreSQL |
| 5900 | TCP | VNC |
| 8080 | TCP | HTTP Proxy/Alt |

## Defensive Best Practices

1. **Network Segmentation**: Separate critical assets
2. **Principle of Least Privilege**: Minimal necessary access
3. **Encryption in Transit**: TLS 1.2+ everywhere
4. **Monitoring & Logging**: Centralized logging, alerting
5. **Regular Patching**: Network devices, OS, applications
6. **Vulnerability Scanning**: Continuous assessment
7. **Incident Response Plan**: Tested and updated
8. **Security Awareness**: Training for all personnel