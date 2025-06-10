# frpc Centralized Panel

## Overview
frpc Centralized Panel is a Gradio-based web platform that unifies the management of multiple frpc clients and their TOML configuration files.  
Traditionally, you’d launch frpc in a shell and manually edit TOML files for each tunnel. In scenarios with multiple servers (e.g. one with high bandwidth but high latency, another with low latency but limited bandwidth), managing separate frpc instances becomes tedious.  
This project combines a visual Gradio interface with MCP (Multi-Chain-Protocol) command support, so you can upload binaries, edit configs, start/stop services, and monitor logs—all in one place.

## Key Features
- 📁 Centralized Management  
  Maintain all frpc tunnels and binaries from a single dashboard.  
- 🛠️ Custom Binary Support  
  Upload and manage unofficial or custom-built frpc executables.  
- 📜 Native TOML  
  Use the standard frp TOML format—no extra parsing or conversion required.  
- 🌐 Live Monitoring  
  View tunnel statuses and real-time logs via the web UI.  
- 🚀 MCP Integration  
  Execute add/modify/delete operations through MCP commands for faster, scriptable workflows.  
- 💡 Fallback Interface  
  The Gradio UI serves as a reliable backup if your LLM agent encounters an error.

## Terminology
1. **proxies (Tunnels)**  
   Configure public-facing mappings for `tcp`, `udp`, or secure tunnel endpoints like `stcp`.  
2. **visitors (Observers)**  
   Define `visitor` entries to accept incoming secure or P2P tunnels registered on the frps server.  
3. **client_configs (Client Connections)**  
   Manage frpc-to-frps connection settings—address, ports, authentication, web dashboard, and protocols.  
4. **programs (Binary Management)**  
   Upload, store, and version frpc executables. Control start/stop operations and view logs.

## Quick Start
Follow these steps to expose a local RDP service via a TCP tunnel:

1. **Upload frpc Binary**  
   - Go to the **Programs** tab  
   - Upload your frpc executable, assign a name and optional description  

2. **Configure Connection**  
   - Switch to **Client Configs**  
   - Add your frps server address, port, and authentication token  
   - Save the client configuration  

3. **Define Tunnel**  
   - Open the **Proxies** tab  
   - Click “Add Proxy” → choose “TCP”  
   - Set local port (e.g. RDP port 3389) and remote port  
   - Save the tunnel configuration  

4. **Start frpc**  
   - Return to **Programs**  
   - Select your uploaded frpc binary and the client config  
   - Click “Start”  

Your local RDP server is now securely exposed to the Internet.  
Monitor tunnel health and logs in real time under the **Online Monitor** section.

---

Once you’re comfortable, use the integrated MCP commands to batch-create, modify, or delete tunnels and configurations—making large-scale management effortless.