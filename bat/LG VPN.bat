@echo off
SET vpn="LG VPN"
ipconfig | find /i %vpn% && rasphone -h %vpn% || rasphone -d %vpn%
