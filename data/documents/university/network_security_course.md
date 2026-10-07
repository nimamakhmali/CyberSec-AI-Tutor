# Network Security Course - CS445

## Course Information
- **Course**: CS445 - Network Security
- **Institution**: CyberSec University
- **Semester**: Fall 2024
- **Credits**: 3
- **Prerequisites**: CS341 (Computer Networks), CS350 (Operating Systems)

## Learning Objectives
By the end of this course, students will be able to:
1. Analyze common network protocols for security vulnerabilities
2. Design and implement network security architectures
3. Configure and manage firewalls, IDS/IPS, and VPNs
4. Perform network traffic analysis and anomaly detection
5. Understand and apply cryptographic protocols in network security
6. Conduct basic penetration testing and vulnerability assessment
7. Develop incident response procedures for network incidents

## Weekly Schedule

### Week 1: Introduction & Threat Model
- Course overview and expectations
- CIA triad in network context
- Threat modeling: STRIDE, PASTA
- Attack surface analysis
- **Reading**: Chapter 1-2, RFC 4949

### Week 2: Network Protocol Security - Link & Network Layer
- ARP spoofing and defenses (DAI, port security)
- IPv4/IPv6 security issues
- ICMP attacks and rate limiting
- DHCP snooping, IP source guard
- **Lab**: ARP spoofing detection with Wireshark

### Week 3: Transport Layer Security
- TCP vulnerabilities: SYN flood, RST injection, sequence prediction
- UDP amplification attacks
- TCP/IP stack hardening
- **Lab**: SYN flood simulation and mitigation

### Week 4: Firewall Fundamentals
- Packet filtering vs stateful inspection
- iptables/nftables rule design
- Zone-based firewalls
- Default deny policies
- **Lab**: Build a multi-zone firewall with nftables

### Week 5: Intrusion Detection & Prevention
- Signature-based vs anomaly-based detection
- Snort/Suricata rule writing
- Network-based vs host-based IDS
- Alert tuning and false positive reduction
- **Lab**: Write custom Suricata rules

### Week 6: VPN Technologies
- IPsec: AH, ESP, IKEv1/v2
- SSL/TLS VPNs
- WireGuard protocol analysis
- VPN deployment architectures
- **Lab**: Configure site-to-site WireGuard

### Week 7: Wireless Security
- 802.11 security evolution: WEP → WPA → WPA2 → WPA3
- WPA2 4-way handshake and KRACK
- Enterprise authentication (802.1X, EAP)
- Wireless IDS/WIPS
- **Lab**: Capture and analyze WPA2 handshake

### Week 8: Midterm Exam

### Week 9: Application Layer Security
- DNS security: DNSSEC, DoH, DoT
- HTTP/HTTPS security: HSTS, CSP, certificate pinning
- Email security: SPF, DKIM, DMARC
- TLS/SSL: Versions, cipher suites, certificate validation
- **Lab**: TLS configuration and testing with testssl.sh

### Week 10: Network Access Control
- 802.1X port-based authentication
- RADIUS/TACACS+ 
- Network Admission Control (NAC)
- Zero Trust Network Access (ZTNA)
- **Lab**: Configure FreeRADIUS with 802.1X

### Week 11: Network Monitoring & Analysis
- NetFlow/IPFIX/sFlow
- Zeek (Bro) network security monitoring
- Threat hunting with network data
- Anomaly detection with ML
- **Lab**: Network traffic analysis with Zeek

### Week 12: DDoS Attack & Defense
- Attack types: volumetric, protocol, application layer
- Amplification/reflection attacks
- Mitigation: scrubbing centers, anycast, rate limiting
- **Lab**: DDoS simulation (controlled environment)

### Week 13: Advanced Topics
- Software-Defined Networking (SDN) security
- Network Function Virtualization (NFV) security
- Container/CNI network security
- Service mesh (Istio/Linkerd) mTLS
- **Guest Lecture**: Industry practitioner

### Week 14: Incident Response
- Network forensics methodology
- PCAP analysis for incident response
- Timeline reconstruction
- Evidence preservation
- **Lab**: Network forensics challenge

### Week 15: Project Presentations & Review
- Student project presentations
- Course review
- Final exam preparation

### Week 16: Final Exam

## Assignments

### Lab Assignments (30%)
1. **Lab 1**: Wireshark fundamentals (Week 2)
2. **Lab 2**: nftables firewall configuration (Week 4)
3. **Lab 3**: Suricata rule writing (Week 5)
4. **Lab 4**: WireGuard VPN setup (Week 6)
5. **Lab 5**: TLS configuration audit (Week 9)
6. **Lab 6**: Network forensics challenge (Week 14)

### Homework (20%)
- Weekly problem sets covering theory and analysis
- Reading summaries for assigned papers

### Midterm Exam (20%)
- In-class, closed book
- Covers Weeks 1-7

### Final Project (20%)
**Network Security Design Project**:
- Design a secure network architecture for a fictional organization
- Include: network diagram, firewall rules, IDS/IPS placement, VPN design, monitoring strategy
- Written report (10-15 pages) + 15-minute presentation
- Team of 2-3 students

### Final Exam (10%)
- Cumulative, emphasis on Weeks 9-14

## Required Textbooks
1. **Network Security Essentials** by William Stallings (7th Edition)
2. **Computer Networking: A Top-Down Approach** by Kurose & Ross (8th Edition) - Reference

## Recommended Reading
- **TCP/IP Illustrated, Volume 1** by Stevens & Fall
- **Practical Packet Analysis** by Chris Sanders
- **Network Security Monitoring** by Richard Bejtlich
- **Applied Network Security Monitoring** by Sanders & Smith

## Tools Used
- Wireshark / TShark
- Nmap / Nping
- iptables / nftables
- Suricata / Snort
- WireGuard / OpenVPN
- Zeek
- OpenSSL / testssl.sh
- FreeRADIUS
- VirtualBox / VMware (lab environment)

## Lab Environment
All labs conducted in isolated virtual environment:
- **Attacker VM**: Kali Linux
- **Target VMs**: Ubuntu Server, Windows Server 2022
- **Network Devices**: VyOS (router/firewall), OpenWrt (AP)
- **Monitoring**: Security Onion (Zeek, Suricata, Elastic)

## Academic Integrity
- All work must be original
- Collaboration allowed on labs only (individual submissions)
- Unauthorized access to systems = immediate failure
- Responsible disclosure required for any discovered vulnerabilities

## Resources
- Course GitHub: github.com/cybersec-university/cs445
- Lab VMs: Available on course server
- Office Hours: Tuesdays 2-4pm, Thursdays 10-12pm
- Discord: #cs445-network-security

## Grading Scale
- A: 93-100%
- A-: 90-92%
- B+: 87-89%
- B: 83-86%
- B-: 80-82%
- C+: 77-79%
- C: 73-76%
- C-: 70-72%
- D: 60-69%
- F: <60%