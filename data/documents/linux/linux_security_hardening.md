# Linux Security Hardening Guide

## User & Access Management

### Sudo Configuration
```bash
# Edit sudoers safely
visudo

# Require password for sudo
Defaults timestamp_timeout=5
Defaults passwd_tries=3

# Log sudo usage
Defaults logfile="/var/log/sudo.log"
```

### SSH Hardening
```bash
# /etc/ssh/sshd_config
Port 22
Protocol 2
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers adminuser
```

### User Account Security
```bash
# Lock unused accounts
usermod -L -e 1 daemon
usermod -L -e 1 bin

# Password policies
# /etc/login.defs
PASS_MAX_DAYS 90
PASS_MIN_DAYS 7
PASS_WARN_AGE 14

# /etc/pam.d/common-password
password requisite pam_pwquality.so retry=3 minlen=12 difok=3 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1
```

## File System Security

### Permissions & Ownership
```bash
# Find world-writable files
find / -type f -perm -002 -ls

# Find SUID/SGID files
find / -type f \( -perm -4000 -o -perm -2000 \) -ls

# Secure critical files
chmod 644 /etc/passwd /etc/group
chmod 600 /etc/shadow /etc/gshadow
chmod 644 /etc/fstab
```

### Mount Options
```bash
# /etc/fstab - Add security options
# tmpfs with noexec,nosuid,nodev
tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev 0 0
tmpfs /var/tmp tmpfs defaults,noexec,nosuid,nodev 0 0

# Remount /home with nodev
/dev/sda2 /home ext4 defaults,nodev 0 2
```

## Kernel Hardening

### sysctl Configuration
```bash
# /etc/sysctl.d/99-security.conf
# Network
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Kernel
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.unprivileged_bpf_disabled = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0
```

### Apply Changes
```bash
sysctl --system
```

## Firewall Configuration

### nftables (Modern)
```bash
#!/bin/bash
# /etc/nftables.conf
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iif "lo" accept
        ct state established,related accept
        ct state invalid drop
        tcp dport 22 accept
        icmp type echo-request limit rate 5/second accept
    }
    chain forward {
        type filter hook forward priority 0; policy drop;
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### Load Rules
```bash
nft -f /etc/nftables.conf
systemctl enable nftables
```

## Audit & Monitoring

### Auditd Configuration
```bash
# /etc/audit/rules.d/audit.rules
# Delete all existing rules
-D

# Buffer size
-b 8192

# Failure mode
-f 1

# Monitor authentication
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Monitor network config
-w /etc/ssh/sshd_config -p wa -k network
-w /etc/hosts -p wa -k network

# Monitor privileged commands
-a always,exit -F arch=b64 -S execve -C uid!=euid -F euid=0 -k setuid
-a always,exit -F arch=b32 -S execve -C uid!=euid -F euid=0 -k setuid
```

### Log Monitoring
```bash
# Centralized logging with rsyslog
# /etc/rsyslog.d/50-security.conf
auth.*,authpriv.* /var/log/auth.log
*.*;auth,authpriv.none -/var/log/syslog
kern.* -/var/log/kern.log
```

## Mandatory Access Control

### AppArmor
```bash
# Check status
apparmor_status

# Enforce profiles
aa-enforce /etc/apparmor.d/*

# Create custom profile for application
# /etc/apparmor.d/usr.local.bin.myapp
#include <tunables/global>
profile myapp /usr/local/bin/myapp {
  #include <abstractions/base>
  /usr/local/bin/myapp r,
  /etc/myapp/config r,
  /var/log/myapp/** w,
}
```

### SELinux (RHEL/Fedora)
```bash
# Check status
sestatus

# Set enforcing mode
setenforce 1
# /etc/selinux/config
SELINUX=enforcing
```

## Service Hardening

### Disable Unused Services
```bash
# List enabled services
systemctl list-unit-files --state=enabled

# Disable unnecessary
systemctl disable --now cups
systemctl disable --now avahi-daemon
systemctl disable --now bluetooth
```

### systemd Service Hardening
```ini
# /etc/systemd/system/myapp.service
[Service]
# Security
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictNamespaces=yes
RestrictRealtime=yes
MemoryDenyWriteExecute=yes
LockPersonality=yes
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
```

## Package Management

### Automatic Updates
```bash
# Ubuntu/Debian - unattended-upgrades
apt install unattended-upgrades
dpkg-reconfigure unattended-upgrades

# RHEL/Fedora - dnf-automatic
dnf install dnf-automatic
systemctl enable --now dnf-automatic.timer
```

### Verify Package Integrity
```bash
# Debian/Ubuntu
debsums -c

# RHEL/Fedora
rpm -Va
```

## Intrusion Detection

### AIDE (Advanced Intrusion Detection Environment)
```bash
# Install
apt install aide

# Initialize database
aideinit

# Check
aide --check
```

### Lynis Auditing
```bash
# Install
apt install lynis

# Run audit
lynis audit system
```

## Container Security

### Docker Hardening
```bash
# Run as non-root
USER 1000

# Read-only filesystem
docker run --read-only ...

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE ...

# Security options
docker run --security-opt=no-new-privileges ...
```

## Compliance

### CIS Benchmarks
- Download CIS Benchmark for your distribution
- Use automated tools: `cis-cat`, `open-scap`

### OpenSCAP
```bash
# Install
apt install libopenscap8 scap-security-guide

# Scan
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```