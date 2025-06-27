## Introduction
frpc Centralized Panel is a Gradio-based centralized management platform designed to unify the administration of multiple frpc instances and their configuration files.
In traditional setups, users must start frpc in the shell and manually edit different TOML configurations to maintain multiple tunnels.
When managing multiple servers (for example, one with high bandwidth/high latency and another with low latency/low bandwidth), the administrative overhead can increase dramatically.
This project combines MCP (Model Context Protocol) interactions with a Gradio visual interface, allowing you to effortlessly handle the entire workflow—uploading programs, configuring, launching, and monitoring.

## Key Features
- 📁 Centralized Management: Maintain all frpc tunnels and programs in one place  
- 🛠 Custom Hosting: Supports uploading and managing unofficially compiled frpc binaries  
- 📜 Native TOML: Uses the official FRP TOML configuration, no extra format conversion needed  
- 🌐 Tunnel Status: The panel queries tunnel online status via frpc’s built-in web server  
- 🚀 MCP Integration: Quickly add, delete, or modify tunnels through MCP commands for increased efficiency  
- 💡 Fallback Option: The Gradio interface serves as a backup management console if the LLM encounters errors  