import gradio as gr
from gradio_mcp.proxies import (
    get_all_proxy,
    get_proxy_by_name,
    get_proxy_by_program_id,
    new_proxy,
    update_proxy_by_name,
    delete_proxy_by_name
)
from gradio_mcp.programs import (
    list_programs,
    program_controller,
    delete_program,
)

def page_chat_ai():
    gr.Markdown("# 这是AI 对话")

def page_clients():
    gr.Markdown("# 这是Frpc客户端配置文件配置")
    
    # gr.Markdown("## get_all_clients")
    # gr.Interface(
    #     fn = get_all_clients,
    #     inputs = None,
    #     outputs = "text"
    # )

def page_proxies():
    gr.Markdown("## get_all_proxy")
    gr.Interface(
        fn = get_all_proxy,
        inputs = None,
        outputs = "text"
    )
    
    gr.Markdown("## get_proxy_by_client_id")
    gr.Interface(
        fn = get_proxy_by_program_id,
        inputs = "text",
        outputs = "text"
    )
    
    gr.Markdown("## get_proxy_by_name")
    gr.Interface(
        fn = get_proxy_by_name,
        inputs = ["text", "text"],
        outputs = "text"
    )
    
    gr.Markdown("## new_proxy")
    gr.Interface(
        fn = new_proxy,
        inputs = ["text", "text"],
        outputs = "text"
    )
    
    gr.Markdown("## update_proxy_by_name")
    gr.Interface(
        fn = update_proxy_by_name,
        inputs = ["text", "text"],
        outputs = "text"
    )

    gr.Markdown("## delete_proxy_by_name")
    gr.Interface(
        fn = delete_proxy_by_name,
        inputs = ["text", "text"],
        outputs = "text"
    )

def page_visitors():
    gr.Markdown("# 观察者(visitors)配置")

def page_programs():
    gr.Markdown("# 客户端配置")
    gr.Markdown("## list_programs")
    gr.Interface(
        fn = list_programs,
        inputs = None,
        outputs = "text"
    )
    
    gr.Markdown("## program_controller")
    gr.Interface(
        fn = program_controller,
        inputs = ["text", "text"],
        outputs = "text"
    )
    
    gr.Markdown("## delete_program")
    gr.Interface(
        fn = delete_program,
        inputs = "text",
        outputs = "text"
    )

with gr.Blocks() as demo:
    gr.Markdown("# 🎉 MCP Server")
    with gr.Tabs():
        with gr.TabItem("AI 对话", id="page1"):
            page_chat_ai()
        with gr.TabItem("隧道(proxies)配置", id="page2"):
            page_proxies()
        with gr.TabItem("观察者(visitors)配置", id="page3"):
            page_proxies()
        with gr.TabItem("客户端配置", id="page4"):
            page_clients()
        with gr.TabItem("客户端配置文件配置", id="page5"):
            page_clients()

if __name__ == "__main__":
    demo.launch(
        mcp_server=True, 
        server_name="0.0.0.0"
    )
