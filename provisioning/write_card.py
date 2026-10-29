#!/usr/bin/env python3
"""
Write an NTAG I2C Plus business-card tag with a dual-platform NDEF message
(vCard record for Android native "add contact" + URL record for iPhone), then
write-protect it with the NTAG 32-bit password (reversible lock).

Requires an ACR122U (or compatible PC/SC) NFC reader and pyscard:
    pip install pyscard

Fill in YOUR details below. Host the .vcf yourself and point VCF_HOST at it.
A USB reader is recommended over a phone: these energy-harvesting cards often
brown out mid-write on a phone's weaker field.
"""
from smartcard.System import readers
from smartcard.util import toHexString as hx

# ---- EDIT THESE -------------------------------------------------------------
NAME  = "Your Name"
ORG   = "Your Company"
PHONE = "+10000000000"
EMAIL = "you@example.com"
SITE  = "https://example.com"              # URL field inside the vCard
VCF_HOST = "example.com/you.vcf"           # hosted .vcf, text after https://
PWD  = [0x12, 0x34, 0x56, 0x78]            # 4-byte NTAG password - CHANGE THIS
PACK = [0x00, 0x00]                        # 2-byte password-acknowledge
# -----------------------------------------------------------------------------

vcard = ("BEGIN:VCARD\r\nVERSION:3.0\r\nFN:%s\r\nORG:%s\r\n"
         "TEL;TYPE=CELL:%s\r\nEMAIL:%s\r\nURL:%s\r\nEND:VCARD\r\n"
         % (NAME, ORG, PHONE, EMAIL, SITE)).encode()
mime = b"text/vcard"
r1 = bytes([0x92, len(mime), len(vcard)]) + mime + vcard      # vCard MIME (MB,SR)
uri = bytes([0x04]) + VCF_HOST.encode()                        # 0x04 = https://
r2 = bytes([0x51, 0x01, len(uri), 0x55]) + uri                 # URI record (ME,SR)
msg = r1 + r2
tlv = bytes([0x03, len(msg)]) + msg + bytes([0xFE])
data = tlv + bytes((-len(tlv)) % 4)
CC = [0xE1, 0x10, 0x6D, 0x00]                                  # NDEF-capable CC

rdr = next((r for r in readers() if "ACR122" in str(r)), None)
if not rdr:
    raise SystemExit("No ACR122U reader found")
c = rdr.createConnection(); c.connect()
def T(a):
    d, s1, s2 = c.transmit(a)
    if s1 != 0x90:
        raise SystemExit("reader error sw=%02X%02X" % (s1, s2))
    return d

print("UID:", hx(T([0xFF, 0xCA, 0x00, 0x00, 0x00])))
# if the tag is already password-protected, authenticate first
if T([0xFF, 0xB0, 0x00, 0xE3, 0x04])[3] <= 0xEB:
    c.transmit([0xFF, 0x00, 0x00, 0x00, 0x07, 0xD4, 0x42, 0x1B] + PWD)

T([0xFF, 0xD6, 0x00, 0x03, 0x04] + CC)                         # capability container
page = 4
for i in range(0, len(data), 4):
    T([0xFF, 0xD6, 0x00, page, 0x04] + list(data[i:i + 4])); page += 1

# password-protect (write only; NFC_PROT=0 keeps it readable). Reversible.
for p, b in [(0xE5, PWD), (0xE6, PACK + [0, 0]), (0xE4, [0, 0, 0, 0]), (0xE3, [0, 0, 0, 0x04])]:
    T([0xFF, 0xD6, 0x00, p, 0x04] + list(b))

# verify it is locked (AUTH0 == 04)
locked = T([0xFF, 0xB0, 0x00, 0xE3, 0x04])[3] == 0x04
print("written and %s" % ("LOCKED (password-protected)" if locked else "NOT LOCKED - check"))
# NOTE: do NOT write the static (page 02h) or dynamic (page E2h) lock bytes unless
# you want the tag PERMANENTLY read-only. Those are one-way over NFC.
