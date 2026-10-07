# Security Tools Reference

## Network Scanning & Reconnaissance

### Nmap
**Purpose**: Network discovery, port scanning, service detection, OS fingerprinting

**Key Features**:
- Host discovery (ping sweep, ARP scan)
- Port scanning (SYN, Connect, UDP, SCTP)
- Service version detection (-sV)
- OS detection (-O)
- Nmap Scripting Engine (NSE) for vuln detection, brute force, etc.
- Output formats: normal, XML, grepable, JSON

**Common Commands**:
```bash
# Quick scan
nmap -T4 -F 192.168.1.0/24

# Comprehensive scan
nmap -A -T4 192.168.1.1

# Vulnerability scan
nmap --script vuln 192.168.1.1

# Web app scan
nmap --script http-enum,http-title,http-headers -p 80,443 target.com

# Output to all formats
nmap -oA scan_results 192.168.1.1
```

### Masscan
**Purpose**: Fastest Internet-scale port scanner

```bash
# Scan entire Internet for port 443
masscan 0.0.0.0/0 -p443 --rate 100000

# Scan with banner grabbing
masscan 192.168.1.0/24 -p1-65535 --banners --rate 1000
```

### ZMap
**Purpose**: Fast single-packet network scanner for Internet-wide surveys

## Traffic Analysis

### Wireshark
**Purpose**: GUI packet capture and analysis

**Key Features**:
- Deep protocol dissection
- Display filters (e.g., `http`, `tcp.port == 80`, `dns`)
- Follow TCP/UDP streams
- Export objects (files, certificates)
- VoIP analysis
- TLS decryption with key log file

**Common Filters**:
```
# HTTP traffic
http

# DNS queries
dns.flags.response == 0

# TLS handshakes
tls.handshake.type == 1

# Retransmissions
tcp.analysis.retransmission

# Specific conversation
ip.addr == 192.168.1.1 and ip.addr == 192.168.1.2
```

### TShark (CLI Wireshark)
```bash
# Capture to file
tshark -i eth0 -w capture.pcap

# Read with display filter
tshark -r capture.pcap -Y "http.request"

# Extract fields
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e http.host
```

### Zeek (formerly Bro)
**Purpose**: Network security monitoring, traffic analysis framework

**Output**: Structured logs (conn.log, http.log, dns.log, ssl.log, etc.)

```bash
# Live capture
zeek -i eth0

# Process pcap
zeek -r capture.pcap
```

### tcpdump
**Purpose**: CLI packet capture

```bash
# Capture to file
tcpdump -i eth0 -w capture.pcap

# Read with filter
tcpdump -r capture.pcap "port 80"

# Verbose with timestamps
tcpdump -i eth0 -nn -tttt -v
```

## Web Application Security

### Burp Suite
**Purpose**: Web application testing platform

**Components**:
- **Proxy**: Intercept/modify requests
- **Scanner**: Automated vulnerability scanning
- **Intruder**: Automated attacks (fuzzing, brute force)
- **Repeater**: Manual request manipulation
- **Sequencer**: Token randomness analysis
- **Decoder/Encoder**: Data transformation
- **Comparer**: Diff tool

### OWASP ZAP (Zed Attack Proxy)
**Purpose**: Free, open-source web app scanner

```bash
# Quick scan
zap.sh -quickurl https://target.com -quickout report.html

# Full scan with auth
zap.sh -cmd -quickurl https://target.com -quickout report.html
```

### sqlmap
**Purpose**: Automated SQL injection detection and exploitation

```bash
# Basic detection
sqlmap -u "http://site.com/page?id=1" --batch

# Exploit with dump
sqlmap -u "http://site.com/page?id=1" --dump --batch

# Post data
sqlmap -u "http://site.com/login" --data="user=test&pass=test" --batch
```

### Nikto
**Purpose**: Web server vulnerability scanner

```bash
nikto -h https://target.com
```

### Gobuster / Dirsearch / Feroxbuster
**Purpose**: Directory/file brute-forcing

```bash
# Gobuster
gobuster dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt

# Feroxbuster (faster, recursive)
feroxbuster -u https://target.com -w wordlist.txt
```

## Vulnerability Scanning

### OpenVAS / Greenbone
**Purpose**: Comprehensive vulnerability management

### Nessus
**Purpose**: Commercial vulnerability scanner

### Nuclei
**Purpose**: Template-based vulnerability scanner

```bash
# Scan with all templates
nuclei -u https://target.com -t cves/ -t vulnerabilities/

# Specific template
nuclei -u https://target.com -t cves/2021/CVE-2021-44228.yaml
```

## Exploitation Frameworks

### Metasploit Framework
**Purpose**: Penetration testing framework

**Key Modules**:
- **Exploits**: Code execution, privilege escalation
- **Auxiliary**: Scanners, fuzzers, DoS
- **Post**: Post-exploitation (meterpreter)
- **Payloads**: Shellcode, meterpreter, shells
- **Encoders**: Payload obfuscation
- **NOPs**: Sled generation

```bash
# Start console
msfconsole

# Search modules
search type:exploit platform:windows smb

# Use exploit
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 192.168.1.100
run
```

### Cobalt Strike (Commercial)
**Purpose**: Adversary simulation / Red Team operations

## Password Attacks

### Hashcat
**Purpose**: World's fastest password cracker (GPU accelerated)

```bash
# Dictionary attack
hashcat -m 0 -a 0 hashes.txt wordlist.txt

# Rule-based attack
hashcat -m 0 -a 0 hashes.txt wordlist.txt -r rules/best64.rule

# Mask attack
hashcat -m 0 -a 3 hashes.txt ?u?l?l?l?l?d?d

# Show cracked
hashcat -m 0 hashes.txt --show
```

**Hash Modes**: MD5(0), SHA1(100), SHA256(1400), SHA512(1700), NTLM(1000), bcrypt(3200), etc.

### John the Ripper
**Purpose**: Fast password cracker (CPU optimized)

```bash
# Auto-detect format
john hashes.txt

# With wordlist
john --wordlist=wordlist.txt hashes.txt

# Incremental mode
john --incremental hashes.txt

# Show results
john --show hashes.txt
```

### Hydra
**Purpose**: Online login brute forcer

```bash
# SSH
hydra -l admin -P wordlist.txt ssh://192.168.1.1

# HTTP POST form
hydra -l admin -P wordlist.txt 192.168.1.1 http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"

# RDP
hydra -l admin -P wordlist.txt rdp://192.168.1.1
```

## Wireless Security

### Aircrack-ng Suite
**Purpose**: WiFi security auditing

**Tools**:
- **airmon-ng**: Enable monitor mode
- **airodump-ng**: Capture packets
- **aireplay-ng**: Inject packets (deauth, ARP replay)
- **aircrack-ng**: Crack WEP/WPA keys

```bash
# Enable monitor mode
airmon-ng start wlan0

# Capture handshake
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon

# Deauth to force handshake
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF wlan0mon

# Crack WPA2
aircrack-ng -w wordlist.txt capture-01.cap
```

### Kismet
**Purpose**: Wireless network detector, sniffer, IDS

## Forensics & Incident Response

### Volatility
**Purpose**: Memory forensics framework

```bash
# Image info
vol -f memory.dmp imageinfo

# Process list
vol -f memory.dmp --profile=Win7SP1x64 pslist

# Network connections
vol -f memory.dmp --profile=Win7SP1x64 netscan

# DLLs
vol -f memory.dmp --profile=Win7SP1x64 dlllist
```

### Autopsy / Sleuth Kit
**Purpose**: Digital forensics platform (GUI + CLI)

### Wireshark (again)
**Purpose**: Network forensics, PCAP analysis

### YARA
**Purpose**: Pattern matching for malware identification

```bash
# Scan file
yara rules.yar suspicious_file.exe

# Scan directory
yara -r rules.yar /path/to/scan
```

## SIEM & Log Analysis

### Elastic Stack (ELK)
- **Elasticsearch**: Search/analytics engine
- **Logstash**: Data processing pipeline
- **Kibana**: Visualization

### Splunk
**Purpose**: Commercial log analysis platform

### Graylog
**Purpose**: Open-source log management

### Sigma
**Purpose**: Generic SIEM rule format

## Cloud Security

### ScoutSuite
**Purpose**: Multi-cloud security auditing

```bash
scout aws --profile default
scout azure --subscription-id <id>
scout gcp --project <project>
```

### Prowler
**Purpose**: AWS security assessment

```bash
prowler aws
```

### CloudSploit
**Purpose**: Cloud security configuration monitoring

## Container Security

### Trivy
**Purpose**: Container vulnerability scanner

```bash
# Scan image
trivy image nginx:latest

# Scan filesystem
trivy fs /path/to/project
```

### Grype
**Purpose**: Container/SBOM vulnerability scanner

```bash
grype nginx:latest
```

### Syft
**Purpose**: SBOM (Software Bill of Materials) generator

```bash
syft nginx:latest -o spdx-json
```

### Hadolint
**Purpose**: Dockerfile linter

```bash
hadolint Dockerfile
```

## Code Analysis

### Bandit
**Purpose**: Python security linter

```bash
bandit -r /path/to/project
```

### Semgrep
**Purpose**: Fast, customizable static analysis

```bash
semgrep --config=auto /path/to/project
```

### CodeQL
**Purpose**: Semantic code analysis (GitHub)

## Threat Intelligence

### MISP
**Purpose**: Threat intelligence sharing platform

### OpenCTI
**Purpose**: Open Cyber Threat Intelligence platform

### YARA (again)
**Purpose**: Malware classification

## Automation & Orchestration

### Ansible
**Purpose**: Infrastructure automation

### SOAR Platforms
- **Cortex XSOAR** (Palo Alto)
- **Splunk SOAR** (Phantom)
- **IBM Resilient**
- **D3 Security**

## Reporting

### Dradis
**Purpose**: Collaboration & reporting framework

### Faraday
**Purpose**: Vulnerability management platform

### Custom
- **Pandoc**: Markdown → PDF/Word
- **WeasyPrint**: HTML → PDF
- **Jinja2**: Template rendering

## Legal & Ethical Reminder

**ALL TOOLS LISTED ARE FOR AUTHORIZED TESTING ONLY**

- Only test systems you own or have explicit written permission to test
- Unauthorized access is illegal in most jurisdictions
- Always work within a defined scope
- Document all activities
- Report findings responsibly
- Follow responsible disclosure practices