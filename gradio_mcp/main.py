import gradio as gr
from gradio_mcp.proxies import (
    get_all_proxy,
    get_proxy_by_name,
    get_proxy_by_client_id,
    new_proxy,
    update_proxy_by_name,
    delete_proxy_by_name
)
from gradio_mcp.clients import (
    get_all_clients,
)

def page_chat_ai():
    gr.Markdown("# 这是AI 对话")

def page_client():
    gr.Markdown("# 这是Frpc客户端配置")
    
    gr.Markdown("## get_all_clients")
    gr.Interface(
        fn = get_all_clients,
        inputs = None,
        outputs = "text"
    )

def page_proxy():
    gr.Markdown("## get_all_proxy")
    gr.Interface(
        fn = get_all_proxy,
        inputs = None,
        outputs = "text"
    )
    
    gr.Markdown("## get_proxy_by_client_id")
    gr.Interface(
        fn = get_proxy_by_client_id,
        inputs = "text",
        outputs = "text"
    )
    
    gr.Markdown("## get_proxy_by_name")
    gr.Interface(
        fn = get_proxy_by_name,
        inputs = ["text", "text"],
        outputs = "text"
    )
    
    # gr.Markdown("## new_proxy")
    # gr.Interface(
    #     fn = new_proxy,
    #     inputs = "text",
    #     outputs = "text"
    # )
    
    # gr.Markdown("## update_proxy_by_name")
    # gr.Interface(
    #     fn = update_proxy_by_name,
    #     inputs = "text",
    #     outputs = "text"
    # )

    # gr.Markdown("## delete_proxy_by_name")
    # gr.Interface(
    #     fn = delete_proxy_by_name,
    #     inputs = "text",
    #     outputs = "text"
    # )

with gr.Blocks() as demo:
    gr.Markdown("# 🎉 MCP Server")
    with gr.Tabs():
        with gr.TabItem("AI 对话", id="page1"):
            page_chat_ai()
        with gr.TabItem("隧道配置", id="page2"):
            page_proxy()
        with gr.TabItem("客户端配置", id="page3"):
            page_client()

if __name__ == "__main__":
    demo.launch(
        mcp_server=True, 
        server_name="0.0.0.0"
    )
