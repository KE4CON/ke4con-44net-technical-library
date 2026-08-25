# Book 7 - APRS

*AROC-BOOK-0007 · Revision 0.1 · KE4CON Amateur Radio Operations Center*

*Generated August 25, 2026 · Markdown is the living source of truth.*


---


# 1. What APRS Is, and How It Actually Works

*From a spoken sentence to a radio wave to a dot on a map — every layer, in order, with a real packet decoded byte by byte.*


## What APRS Is, and Why It Isn't 'Just Tracking'

**APRS (Automatic Packet Reporting System)** is a two-way, real-time digital communications system for amateur radio. Bob Bruninga, WB4APR, began developing the concept in the mid-1980s, with the system as it's known today taking shape around 1992. The common misconception is that APRS is a vehicle-tracking system — a ham-radio GPS breadcrumb trail. It isn't, and that distinction matters enough to build a whole chapter around.

> **JARGON, IN PLAIN WORDS** — **Situational awareness** means knowing what is happening around you, right now, without having to ask. A weather radar loop gives a meteorologist situational awareness. A dispatcher's map of every unit's location gives them situational awareness. That is what Bruninga actually built: a way for every station on a channel to maintain a shared, live picture of who and what is out there — positions, yes, but also weather, messages, objects, and resources — updated continuously and automatically, with no one having to call anyone else on voice to ask.

That distinction — situational awareness over tracking — is why APRS transmits redundantly at a **decaying rate**: a moving station beacons often while its position is changing quickly, then less often once it settles, so the network spends its limited airtime on what's actually new. A pure tracker would just log points; APRS is built to keep a shared picture current using the least channel time possible, because the channel is a shared, finite resource every station on frequency has to share.

The rest of this chapter follows one piece of information — a station's position — all the way down through every layer of the system: from the RF modulation that turns a bit into a tone, through the AX.25 frame that wraps it, to the plain-text format that encodes a latitude and longitude, to the digipeater network that relays it, to the Internet gateway that hands it to the rest of the world. By the end, a real packet is decoded byte by byte, and you'll be able to do the same to any packet you capture yourself.


## The Physical Layer: How a Byte Becomes a Radio Wave


### AFSK: two tones, not a shifting carrier

APRS over RF is carried on ordinary FM voice radios — the same rigs used for repeater chats — using **AFSK (Audio Frequency-Shift Keying)**. The distinction in that name matters: in true FSK, the radio's carrier frequency itself shifts between two values. In AFSK, the carrier doesn't move at all; instead, two **audio tones** are fed into the microphone input (or a data port) and the radio's ordinary FM transmitter carries whichever tone is currently playing, exactly as it would carry a human voice. This is precisely why any FM handheld or mobile with a data/packet port — or even just a speaker-mic jack and a TNC — can transmit APRS: nothing about the radio itself needs to know APRS exists.

The specific tone pair is the **Bell 202** standard, a modem tone scheme from 1970s telephone-line data communication that amateur packet radio adopted in the 1980s and never replaced: a **1200 Hz "mark" tone** and a **2200 Hz "space" tone**, switched at **1200 baud** (1200 symbol changes per second — and since each symbol here is one bit, this is also 1200 bits per second).


### NRZI: why a steady tone means '1' and a changing tone means '0'

It would be simple to say "mark tone means bit value 1, space tone means bit value 0" — but that is **not** how AX.25 actually encodes bits onto those two tones. Instead it uses **NRZI (Non-Return-to-Zero Inverted)** encoding, and the rule inverts the intuition:

- A data bit of **`1`** is sent as **no tone change** — whichever tone was already playing keeps playing.
- A data bit of **`0`** is sent as **a tone change** — mark switches to space, or space switches to mark.

> **ENGINEERING NOTE** — Why encode it this way instead of the "obvious" direct mapping? NRZI is what makes **bit stuffing** (covered next) work at all, and bit stuffing is what makes the frame boundary marker (a fixed pattern of six 1-bits) unambiguous no matter what data is inside the frame. A long run of the *same* bit value produces a long run of tone *changes* under NRZI — which is exactly the behavior the receiver's clock-recovery circuit needs to stay synchronized, and exactly the property bit stuffing depends on to guarantee the flag pattern can never appear by accident inside real data.

| Bit stream | Tone sequence (NRZI) |
| --- | --- |
| `1 1 1 0 1` | mark, mark, mark, **space**, space |
| `0 0 1 1 0` | **space**, **mark**, mark, mark, **space** |


### Why 144.390 MHz — and why it's different elsewhere

In North America, essentially all APRS RF activity shares one nationally-coordinated frequency, which is what makes a single mobile digipeater or iGate useful to every APRS station that drives past it. Other ITU regions coordinated a different shared frequency for the same reason — there's nothing technically special about any of these numbers; the value is entirely in everyone agreeing to use the same one.

| Region | Frequency |
| --- | --- |
| North America | 144.390 MHz |
| Europe | 144.800 MHz |
| Australia | 145.175 MHz |


## The Link Layer: AX.25, Packet Radio's Envelope

Everything above this point has been about turning bits into tones. **AX.25** ('Amateur X.25' — a link-layer protocol adapted from the ITU-T X.25 packet standard for ham radio) is what turns those bits into a structured, addressed, checksummed *frame* — an envelope with a "from," a "to," routing instructions, and a payload, the same conceptual job an Ethernet or Wi-Fi frame does for computer networks.

APRS uses exactly one AX.25 frame type: the connectionless **UI (Unnumbered Information) frame**. AX.25 also supports connection-oriented, numbered frames (for a reliable two-station link, like a BBS session) — APRS deliberately doesn't use any of that machinery, because a position report is a one-shot broadcast to everyone listening, not a private session with one other station.

| Field | Size | Contents |
| --- | --- | --- |
| Flag | 1 byte | `0x7E` — marks the start of the frame |
| Destination address | 7 bytes | Callsign + SSID (conventionally `APRS` or a software-ID string, not a real station) |
| Source address | 7 bytes | The transmitting station's callsign + SSID |
| Digipeater address(es) | 0–56 bytes | Up to 8 relay-path entries, 7 bytes each |
| Control | 1 byte | `0x03` — UI frame |
| PID | 1 byte | `0xF0` — no layer-3 protocol |
| Information | up to 256 bytes | The actual APRS data — position, message, weather, etc. |
| FCS | 2 bytes | CRC-16 checksum, protecting everything from the destination address through the information field |
| Flag | 1 byte | `0x7E` — marks the end of the frame |


### Callsigns packed into seven bytes

Each address — destination, source, or digipeater — is exactly 7 bytes: a 6-byte callsign field, then 1 SSID byte. The callsign is padded to 6 characters with spaces if shorter, and every character is **left-shifted by one bit** before being placed in the frame (this shift exists so the low bit of every callsign byte is free to be used as a flag elsewhere in the protocol). The 7th byte packs the **SSID (Secondary Station Identifier, 0–15)** — the number hams add after a callsign, like `-9`, to distinguish multiple stations or purposes under one license — together with two structural bits:

```
Bit:     7  6  5  4  3  2  1  0
Value:   1  1  1  S  S  S  S  L

  bits 7-5: always 1 1 1 (reserved)
  bits 4-1: SSID value, 0-15
  bit 0 (L): end-of-address bit
             0 = more addresses follow
             1 = this is the last address in the frame
```

So a source address of **`KE4CON-9`** is packed as the shifted bytes for `K`, `E`, `4`, `C`, `O`, `N`, followed by an SSID byte encoding the value 9 and the end-of-address bit — set to `1` only if no digipeater addresses follow it in the frame.


### Bit stuffing: keeping real data from impersonating a flag

The flag byte, `0x7E`, is the bit pattern `01111110` — six consecutive `1` bits. If that exact six-`1` run could ever occur naturally inside the frame's own data, a receiver would misread the middle of a frame as its end. AX.25 prevents this with **bit stuffing**: after transmitting five consecutive `1` bits anywhere between the opening and closing flags, the transmitter inserts an extra `0` bit that carries no data at all. The receiver does the reverse — after five consecutive `1` bits, it discards the next bit before it ever inserts a `0`. The flag bytes themselves are exempt from this rule, which is exactly why a flag can never be confused with stuffed data: six-or-more consecutive `1` bits appears in the actual transmitted bitstream *only* at a flag.


### The information field and the checksum

The **information field** is where the actual APRS content lives — and unlike the address fields, its characters are plain, un-shifted ASCII. The **FCS (Frame Check Sequence)** is a 16-bit CRC (per ISO 3309), computed most-significant-bit-first and transmitted inverted, covering every byte from the destination address through the end of the information field. If a receiver recomputes the CRC over a received frame and it doesn't match the transmitted FCS, the frame is corrupted — most likely from another station transmitting at the same instant (a collision) — and is simply discarded. AX.25 has no retransmission mechanism for UI frames; a lost APRS packet is just gone, which is one more reason the whole system is built around frequent, redundant, decaying-rate updates rather than any single packet being guaranteed to arrive.


## The Application Layer: What's Actually Inside a Position Packet


### Position reports: turning a lat/lon into text a radio can send

The information field's first character is a **Data Type Identifier** that tells a receiving station what kind of APRS data follows — a position, a message, a weather report, an object, and more. Two of the most common are `!` (a real-time position report, no timestamp) and `@` (a position report **with** a timestamp, used when the report describes where a station *was* at a specific time rather than right now).

A real, complete uncompressed position report looks like this:

```
!4903.50N/07201.75W>Test1234
```

Decoded field by field:

| Characters | Meaning |
| --- | --- |
| `!` | Data type identifier — real-time position, no timestamp |
| `4903.50N` | Latitude: 49 degrees, 3.50 minutes North (the format is fixed-width `ddmm.hh` + `N`/`S`) |
| `/` | Symbol table identifier — `/` selects the **primary** symbol table |
| `07201.75W` | Longitude: 072 degrees, 1.75 minutes West (fixed-width `dddmm.hh` + `E`/`W`) |
| `>` | Symbol code — on the primary table, `>` renders as a car icon on a map |
| `Test1234` | Free-text comment — up to 40 characters, shown alongside the station on a map or in a station list |


### Symbol tables: one character chooses the icon

APRS defines two symbol tables — **primary** (selected with `/`) and **alternate** (selected with `\`) — each holding dozens of single-character icon codes (a car, a house, a digipeater, a weather station, and many more). The symbol table character and the symbol code character together are what a mapping application — like the one built into APRS-Command — uses to choose which icon to draw at a station's reported position.

> **SCOPE NOTE FOR THIS CHAPTER** — APRS also defines a **compressed** position format — a denser encoding (using a base-91 numbering scheme) that packs latitude, longitude, and optionally course/speed or altitude into fewer bytes than the fixed-width format shown above. It's real, it's in daily use, and it deserves its own full treatment — deliberately left to a later chapter rather than folded in here at reduced rigor.


## The Network Layer: How One Packet Reaches an Entire Region


### Digipeating: radios relaying radios

A single APRS station transmitting at typical handheld or mobile power might reach a few miles. To cover a region, APRS relies on **digipeaters** — stations, usually on hilltops or towers, that simply repeat any packet whose digipeater address field names them, then remove their own callsign from that field (or decrement a counter, covered next) so the packet isn't repeated by the same digipeater twice.


### The New-N Paradigm: WIDE2-2 and WIDE1-1,WIDE2-1

Early APRS used generic aliases like `RELAY` and `WIDE`, and operators would often chain several of them together (`WIDE,WIDE,WIDE`) hoping for wider reach — which instead flooded busy areas with duplicate packets as every digipeater in range repeated every hop. National operating rules were standardized around 2004 under the **New-N Paradigm** specifically to eliminate that inefficient routing.

The New-N Paradigm uses a **generic alias with a built-in hop-count**, written `WIDEn-N` — for example `WIDE2-2` means "repeat this up to 2 more times, generically." Each time a digipeater repeats the packet, it decrements that trailing number by one; once it reaches zero, no further digipeater will repeat it. The current guidance:

- **`WIDE2-2`** — a general-purpose 2-hop path, the recommended default in essentially all areas for a station with no specific local knowledge of the digipeater network around it.
- **`WIDE1-1,WIDE2-1`** — a specialized 2-hop path for mobiles that have a nearby **fill-in digipeater** (a lower-power, local-coverage digipeater that only responds to `WIDE1-1`), letting that local digipeater pick the packet up first before it's repeated once more onto the wider regional network.


### APRS-IS: where RF meets the Internet

Digipeating alone only reaches as far as the RF network extends. **APRS-IS (the APRS Internet System)** is a worldwide, Internet-connected network of servers that any station can connect to directly, and that an **iGate** — a station configured to bridge the two worlds — feeds with everything it hears over RF. This is why a station transmitting nothing but a 5-watt handheld on a hilltop can still show up, moments later, on a map viewed from anywhere in the world: RF got the packet to one iGate, and APRS-IS carried it the rest of the way.


## Seeing It Work: APRS-Command as a Reference Implementation

Every layer described in this chapter is real, working code in **APRS-Command**, the cross-platform APRS client built as part of this project (GPL v3, C# / .NET, Avalonia UI — runs on Windows, macOS, Linux, and Raspberry Pi from one codebase). It's worth connecting the two directly, so this chapter isn't just theory:

| Layer in this chapter | Where it lives in APRS-Command |
| --- | --- |
| Link layer (AX.25 frames, packet parsing) | `src/Aprs.Core` — APRS packet types and parser |
| Physical/transport layer (serial KISS TNC, TCP KISS, AGWPE, APRS-IS) | `src/Aprs.Transport` |
| Digipeating (New-N Paradigm, fill-in and full modes) | `src/Aprs.Services` — configurable digipeater with alias support |
| APRS-IS / iGate bridging | `src/Aprs.Services` — iGate with packet-type filtering |
| Application layer (position reports, symbol tables) | Beacon scheduler + symbol picker in `src/Aprs.Desktop`, rendered via `src/Aprs.Mapping` |

The project's own README describes its guiding philosophy in terms that echo exactly what this chapter opened with: APRS-Command exists to give operators "a common operating picture" — situational awareness, not just a tracker — which is the same distinction Bob Bruninga built the whole protocol around forty years earlier.


## Why This Matters for Project AROC

An Amateur Radio Operations Center needs exactly what APRS was designed to provide: a shared, continuously-updating picture of positions, resources, and messages across everyone operating on a network — the same need behind Book 6 (Operations) and Book 10 (Emergency Communications). Understanding APRS from the tone pair up, not just as "the app that shows dots on a map," is what makes it possible to actually design, troubleshoot, and extend an operations center that depends on it — placing a digipeater, choosing a path, diagnosing why a station isn't showing up, or deciding whether a feature belongs in APRS-Command at all.

> **DESIGN TAKEAWAY** — Every layer in this chapter exists to solve one specific, real problem: AFSK/Bell 202 lets APRS ride on ordinary FM voice radios; NRZI and bit stuffing make the frame boundary unambiguous; AX.25's UI frame skips connection overhead a one-shot broadcast doesn't need; the New-N Paradigm exists because the old alternative flooded the airwaves; and APRS-IS exists because RF range alone was never going to be global. None of it is arbitrary — and that's the pattern worth carrying into every other chapter of this library.


## Sources & Further Reading

- aprs.org — Bob Bruninga's original APRS reference site: http://www.aprs.org/
- aprs.org — The New-N Paradigm: http://www.aprs.org/newN/new-N.html
- APRS Protocol Reference, Version 1.0.1 (APRS101.PDF): https://www.aprs.org/doc/APRS101.PDF
- Kenneth W. Finnegan, W6KWF — "Clarifying the Amateur Bell 202 Modem" (TAPR Digital Communications Conference 2014): https://files.tapr.org/meetings/DCC_2014/DCC2014-Amateur-Bell-202-Modem-W6KWF-and-Bridget-Benson.pdf
- Joshua Jerred — "APRS & AX.25 Demystified: Full Packet Generation and Frame Encoding": https://joshuajer.red/blog/2023-01-04-APRS-and-ax25
- APRS-Command source and documentation: https://github.com/KE4CON/APRS-Command
