# Prebuilt firmware

`nfc_card-attiny816-1MHz.hex`: `../nfc_card.ino` built with megaTinyCore 2.6.10 (arduino-cli 1.1.1),
FQBN `megaTinyCore:megaavr:atxy6:chip=816,clock=1internal` (ATtiny816, 1 MHz internal). 2824 B flash / 71 B RAM.
Indicator-LED Morse easter egg: **STAXXLOGIX.COM**.

Fuses megaTinyCore writes with it (fuse 5/SYSCFG0 is NOT written, so the UPDI pin stays UPDI):
`0 (WDTCFG)=0x00, 2 (OSCCFG)=0x01 (16 MHz base, /16 -> 1 MHz), 6 (SYSCFG1)=0x04, 7 (APPEND)=0x00, 8 (BOOTEND)=0x00`

Flash over SerialUPDI (USB-serial at **3.3 V**: GND->J1 pad 1, 3V3->pad 2, RX direct + TX via 4.7k -> pad 3):
```
pip install pymcuprog
P=/dev/ttyUSB0        # or COM5 on Windows
pymcuprog -t uart -u $P -d attiny816 ping
pymcuprog -t uart -u $P -d attiny816 erase
for f in 0:0x00 2:0x01 6:0x04 7:0x00 8:0x00; do pymcuprog -t uart -u $P -d attiny816 write -m fuses -o ${f%%:*} -l ${f##*:}; done
pymcuprog -t uart -u $P -d attiny816 write -f nfc_card-attiny816-1MHz.hex --verify
```
(Arduino IDE "Upload Using Programmer" with the same board options does all of this in one step.)
