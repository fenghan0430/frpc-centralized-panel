import atexit
import signal
import sys
import gradio as gr
from gradio_mcp.log import logger
from gradio_mcp.proxies import (
    get_all_proxy,
    get_proxy_by_name,
    get_proxy_by_program_id,
    new_proxy,
    update_proxy_by_name,
    delete_proxy_by_name
)
from gradio_mcp.visitors import (
    get_all_visitors,
    get_visitors_by_program_id,
    get_visitor_by_name,
    new_visitor,
    update_visitor_by_name,
    delete_visitor_by_name
)
from gradio_mcp.programs import (
    list_programs,
    program_controller,
    delete_program
)
from gradio_mcp.client_configs import (
    get_client_config_by_id,
    new_client_config,
    update_client_config,
    delete_client_config
)
from utils.program_manager import ProgramManager
    
def page_chat_ai():
    gr.Markdown("# 这是AI 对话")

def page_client_configs():
    gr.Markdown("# 客户端配置文件配置")
    gr.Markdown("## get_client_config_by_id")
    gr.Interface(
        fn=get_client_config_by_id,
        inputs="text",
        outputs="text"
    )
    
    gr.Markdown("## new_client_config")
    gr.Interface(
        fn=new_client_config,
        inputs=["text", "text"],
        outputs="text"
    )
    
    gr.Markdown("## update_client_config")
    gr.Interface(
        fn=update_client_config,
        inputs=["text", "text"],
        outputs="text"
    )
    
    gr.Markdown("## delete_client_config")
    gr.Interface(
        fn=delete_client_config,
        inputs="text",
        outputs="text"
    )

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
    gr.Markdown("# 观察者(visitors)接口列表")

    gr.Markdown("## get_all_visitors")
    gr.Interface(
        fn=get_all_visitors,
        inputs=None,
        outputs="text"
    )
    
    gr.Markdown("## get_visitors_by_program_id")
    gr.Interface(
        fn=get_visitors_by_program_id,
        inputs="text",
        outputs="text"
    )
    
    gr.Markdown("## get_visitor_by_name")
    gr.Interface(
        fn=get_visitor_by_name,
        inputs=["text", "text"],
        outputs="text"
    )

    gr.Markdown("## new_visitor")
    gr.Interface(
        fn=new_visitor,
        inputs=["text", "text"],
        outputs="text"
    )

    gr.Markdown("## update_visitor_by_name")
    gr.Interface(
        fn=update_visitor_by_name,
        inputs=["text", "text"],
        outputs="text"
    )

    gr.Markdown("## delete_visitor_by_name")
    gr.Interface(
        fn=delete_visitor_by_name,
        inputs=["text", "text"],
        outputs="text"
    )

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
            page_visitors()
        with gr.TabItem("客户端配置", id="page4"):
            page_programs()
        with gr.TabItem("客户端配置文件配置", id="page5"):
            page_client_configs()

# TODO: 清除上传缓存

def _cleanup_before_exit(type_: str = ""):
    logger.info(f"收到退出信号{type_}，开始清理工作…")
    program_manager: ProgramManager = ProgramManager()
    program_manager.stop_all()

# 在程序正常退出时也执行一次清理
atexit.register(_cleanup_before_exit)
# 捕获 kill (SIGTERM)
signal.signal(signal.SIGTERM, lambda signum, frame: (_cleanup_before_exit("SIGTERM"), sys.exit(0)))


if __name__ == "__main__":
    demo.launch(
        mcp_server=True, 
        server_name="0.0.0.0"
    )
