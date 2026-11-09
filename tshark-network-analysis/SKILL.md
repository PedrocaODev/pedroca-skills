---
name: tshark-network-analysis
description: Analyzes pcap/pcapng capture files using tshark (Wireshark CLI) for defensive network forensics, traffic inspection, protocol statistics, and troubleshooting. Metadata-first, bounded, read-only.
---

# tshark-network-analysis

## When to load

- Authorized inspection of `.pcap` / `.pcapng` capture files
- Packet/traffic analysis, protocol hierarchy, endpoints, conversations, streams
- Network forensics, flow reconstruction, defensive cybersecurity troubleshooting

## When NOT to load

- Generic internet research or network programming tasks
- Offensive activity, exploitation, or traffic generation
- Tasks that don't involve tshark or capture file analysis

## Rules

### Capture file handling

- Preserve evidence read-only; never alter or delete captures
- Prefer offline analysis of existing files over live capture
- Start narrow: metadata, protocol hierarchy, endpoints, conversations before payloads

### Shell discipline

- Always prefix commands with `rtk`
- Always quote file paths containing spaces
- Bound output: use `-c <count>` or `-T fields` with selected columns
- Prefer focused display filters (`-Y`) over raw payload dumps

### Display filters vs capture filters

- `-Y` = display filter (post-capture analysis). Use this.
- `-f` = capture filter (BPF, live capture only). Mention only when discussing live capture setup.

### Live capture policy

Live capture requires ALL of these before proceeding:
1. Explicit user request and authorization
2. Confirmed interface name (`rtk tshark -D`)
3. Defined output path for the capture file
4. Capture filter specified (or explicitly none)
5. Hard bound: duration (`-a duration:<sec>`), packet count (`-c`), or file size (`-a filesize:<KB>`)

Never start an unbounded capture.

### Permissions

- Never run `sudo` or modify system capabilities/groups silently
- If `dumpcap` permission is denied, report that setup is needed (user may need to join the `wireshark` group or use `setcap`); do not attempt fixes
- On WSL2, only WSL-visible interfaces are available for capture

### Sensitive data

- Treat payloads, credentials, identifiers, and keys as sensitive
- Summarize metadata first; expose stream/payload content only when necessary and explicitly authorized
- Redact or truncate sensitive fields in output when practical

### Reporting

- State exact commands and filters used
- Note key evidence, output limits, and any uncertainty
- Do not install new dependencies or use tshark MCP servers

## Command templates

### Offline overview (metadata-first)

```bash
rtk tshark -r "capture.pcap" -q -z io,stat,0 -z conv,ip -z endpoints,ip
```

### Protocol hierarchy

```bash
rtk tshark -r "capture.pcap" -q -z io,phs
```

### Bounded display-filter read

```bash
rtk tshark -r "capture.pcap" -Y "tcp.port == 443" -c 100 -T fields -e frame.number -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e frame.len
```

### Bounded live capture (requires explicit authorization)

```bash
rtk tshark -i eth0 -f "tcp port 80" -w "/tmp/capture.pcap" -a duration:60 -a filesize:10240
```
