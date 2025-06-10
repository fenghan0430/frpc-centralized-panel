import asyncio
import atexit
import json
import logging
import os
import signal
import sys
import gradio as gr
import pandas as pd
import toml
from gradio_mcp.log import logger 
from gradio_mcp.proxies import (
    get_all_proxies,
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
    new_program,
    program_controller,
    delete_program,
    watch_log
)
from gradio_mcp.client_configs import (
    get_client_config_by_id,
    new_client_config,
    update_client_config,
    delete_client_config
)
from utils.database import DataBase
from utils.program_manager import ProgramManager
    
# 临时配置文件地址
data_path = "data/"
select_tab_id = None
tasks = []

def page_client_configs_mcp():
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

def page_proxies_mcp():
    gr.Markdown("## get_all_proxy")
    gr.Interface(
        fn = get_all_proxies,
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

def page_visitors_mcp():
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

def page_programs_mcp():
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

def init():
    """准备 app"""
    with DataBase(os.path.join(data_path, "data.db")) as db:
        db.init_db()

def get_dp_choices_for_program_name():
  program_list = list_programs()
  if not program_list["status"] == "成功":
    logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
    raise gr.Error("获取程序列表数据错误")
  
  program_id_name_map = {}
  for i in program_list['data']:
    program_id_name_map[i['name']] = str(i['id'])
  return gr.Dropdown(
    choices=list(program_id_name_map.keys()), 
    value=list(program_id_name_map.keys())[0] if len(program_id_name_map.keys()) != 0 else None
    )

def get_program_name_ip_map():
  program_list = list_programs()
  if not program_list["status"] == "成功":
    logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
    raise gr.Error("获取程序列表数据错误")
  program_list = program_list['data'] # list
  
  program_id_name_map = {}
  for i in range(len(program_list)):
    program_id_name_map[program_list[i]['name']] = str(program_list[i]['id'])
  return program_id_name_map

with gr.Blocks(title="frpc 管理面板") as demo:
  gr.Markdown("# 🎉 MCP Server")

  with gr.Tabs():
    
    
    with gr.TabItem("README") as readme_tab:
      gr.Markdown("## README")
    
    
    with gr.Tab("隧道(proxies)管理") as proxies_tab:
      gr.Markdown("## 隧道(proxies)管理界面")
      data_table = gr.Dataframe()
      def get_proxies_table():
        data = get_all_proxies()
        if not data["status"] == "成功":
          logger.error(f"获取隧道数据错误，错误：{data['message']}")
          raise gr.Error("获取隧道数据错误")
        
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
          raise gr.Error("获取程序列表数据错误")
        program_list = program_list['data'] # list
        
        program_id_name_map = {}
        for i in range(len(program_list)):
          program_id_name_map[str(program_list[i]['id'])] = program_list[i]['name']
        
        program_id_remoteIp_map = {}
        for i in program_id_name_map.keys():
          cfg = get_client_config_by_id(i)
          if not cfg["status"] == "成功":
            continue
          cfg = cfg['data']
          program_id_remoteIp_map[i] = cfg['serverAddr']
        
        data = data['data'] # list
        data_pd = pd.DataFrame(columns = ["program name", "name", "type", "status", 'route'])
        if len(data) <= 0:
          data_pd.loc[0] = ["目前没有隧道", "目前没有隧道", "目前没有隧道", "目前没有隧道", "目前没有隧道"]

        for data_item in data:
          if data_item['type'] == "http":
            route = f"http://{ data_item['localIP'] }:{str( data_item['localPort']) } -> http://{ data_item['customDomains'][0] }"
          elif data_item['type'] == "https":
            route = f"https://{ data_item['localIP'] }:{str( data_item['localPort']) } -> https://{ data_item['customDomains'][0] }"
          elif data_item['type'] in ['stcp', "xtcp", 'sudp']:
            route = f"{ data_item['localIP'] }:{str( data_item['localPort'] )} -> {data_item['name']}"
          else:
            route = f"{ data_item['localIP'] }:{str( data_item['localPort'] )} -> {program_id_remoteIp_map[str(data_item['program_id'])]}:{data_item['remotePort']}"
          
          data_pd.loc[len(data_pd)] = [program_id_name_map[str(data_item['program_id'])], data_item['name'], data_item['type'], data_item['status'], route]
        
        return gr.Dataframe(value = data_pd)
      
      proxies_tab.select(fn=get_proxies_table, outputs=data_table, show_api=False)
      
      with gr.Tab("新建隧道") as new_proxy_tab:
        with gr.Row():
          dp_program_id_new = gr.Dropdown(interactive=True)

          new_proxy_tab.select(fn=get_dp_choices_for_program_name, outputs=dp_program_id_new, show_api=False)
          
          def new_proxy_from_code(pname, toml_str):
            cfg = toml.loads(toml_str)
            cfg = json.dumps(cfg, ensure_ascii=False)
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = new_proxy(program_id_name_map[pname], cfg)
            if msg['status'] == '成功':
              gr.Success(msg['message'])
            else:
              raise gr.Error(msg['message'])
          btn_new = gr.Button("新建隧道")
        
        code = gr.Code(label="隧道参数(格式toml)", interactive=True)
        btn_new.click(fn=new_proxy_from_code, inputs=[dp_program_id_new, code], show_api=False)
      with gr.Tab("修改/删除隧道") as change_proxy_tab:
        with gr.Row():
          dp_program_id_change = gr.Dropdown(interactive=True)
          change_proxy_tab.select(
            fn=get_dp_choices_for_program_name, 
            outputs=dp_program_id_change, 
            show_api=False
            )
          
          dp_proxy_name = gr.Dropdown(interactive=True)
          
          def get_dp_choices_for_proxies(pname):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = get_proxy_by_program_id(program_id_name_map[pname])
            if not msg['status'] == '成功':
              logger.error(f"获取代理数据错误，错误：{msg['message']}")
              raise gr.Error("获取代理数据错误")
            names = []
            
            for i in msg['data']:
              names.append(i['name'])
            return gr.Dropdown(choices=names, value= names[0] if len(names) > 0 else None)
          dp_program_id_change.change(
            fn=get_dp_choices_for_proxies, 
            inputs=[dp_program_id_change], 
            outputs=dp_proxy_name, 
            show_api=False
            )
          
          def get_proxy_config_for_code(pname, name):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = get_proxy_by_name(program_id_name_map[pname], name)
            if not msg['status'] == '成功':
              logger.error(f"获取隧道配置数据错误，错误：{msg['message']}")
              raise gr.Error("获取隧道配置数据")

            data = toml.dumps(msg['data'])
            
            return gr.Code(data)
            
          def update_proxy_from_code(pname, config):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            data = json.dumps(toml.loads(config), ensure_ascii=False)

            msg = update_proxy_by_name(program_id_name_map[pname], data)
            if not msg['status'] == "成功":
              logger.error(f"更新隧道配置数据错误，错误：{msg['message']}")
              raise gr.Error(f"更新隧道配置数据，错误：{msg['message']}")
            gr.Success(msg['message'])
          
          def del_proxy(pname, name):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = delete_proxy_by_name(program_id_name_map[pname], name)
            if not msg['status'] == "成功":
              logger.error(f"删除隧道出现错误，错误：{msg['message']}")
              raise gr.Error(f"删除隧道出现错误，错误：{msg['message']}")
            gr.Success(msg['message'])
          
          btn_get_proxy_config = gr.Button("获取隧道配置")
          btn_update_proxy = gr.Button("更新隧道配置", variant='huggingface')
          btn_del_proxy = gr.Button('删除隧道', variant='stop')
        
        code_proxy_change = gr.Code(interactive=True)
        
        btn_get_proxy_config.click(
          fn=get_proxy_config_for_code, 
          inputs=[dp_program_id_change, dp_proxy_name], 
          outputs=code_proxy_change,
          show_api=False
          )
        btn_update_proxy.click(
          fn=update_proxy_from_code, 
          inputs = [dp_program_id_change, code_proxy_change],
          show_api=False
        )
        btn_del_proxy.click(
          fn=del_proxy,
          inputs=[dp_program_id_change, dp_proxy_name],
          show_api=False
          )
      
      proxies_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_new, 
        show_api=False
        )
      
      
    with gr.Tab("观察者(visitors)管理") as visitors_tab:
      gr.Markdown("## 观察者(visitors)管理界面")
      visitors_data_table = gr.Dataframe()
      def get_visitors_table():
        data = get_all_visitors()
        if not data["status"] == "成功":
          logger.error(f"获取观察者数据错误，错误：{data['message']}")
          raise gr.Error("获取观察者数据错误")
        
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
          raise gr.Error("获取程序列表数据错误")
        program_list = program_list['data'] # list
        
        program_id_name_map = {}
        for i in range(len(program_list)):
          program_id_name_map[str(program_list[i]['id'])] = program_list[i]['name']
        
        program_id_remoteIp_map = {}
        for i in program_id_name_map.keys():
          cfg = get_client_config_by_id(i)
          if not cfg["status"] == "成功":
            continue
          cfg = cfg['data']
          program_id_remoteIp_map[i] = cfg['serverAddr']
        
        data = data['data'] # list
        data_pd = pd.DataFrame(columns = ["program name", "name", "type", 'route'])
        if len(data) <= 0:
          data_pd.loc[0] = ["目前没有观察者", "目前没有观察者", "目前没有观察者", "目前没有观察者"]
        for data_item in data:
          route = f"{data_item['serverName']} -> {data_item['bindAddr']}:{data_item['bindPort']}"
          data_pd.loc[len(data_pd)] = [program_id_name_map[str(data_item['program_id'])], data_item['name'], data_item['type'], route]
        
        return gr.Dataframe(value = data_pd)
      
      visitors_tab.select(fn=get_visitors_table, outputs=visitors_data_table, show_api=False)

      with gr.Tab("新建观察者") as new_visitor_tab:
        with gr.Row():
          dp_program_id_new_visitor = gr.Dropdown(interactive=True)
          new_visitor_tab.select(
            fn=get_dp_choices_for_program_name, 
            outputs=dp_program_id_new_visitor, 
            show_api=False
            )
          
          def new_visitor_from_code(pname, toml_str):
            cfg = toml.loads(toml_str)
            cfg = json.dumps(cfg, ensure_ascii=False)
            
            program_name_id_map = get_program_name_ip_map()
            
            msg = new_visitor(program_name_id_map[pname], cfg)
            if msg['status'] == '成功':
              gr.Success(msg['message'])
            else:
              raise gr.Error(msg['message'])
          
          btn_new_visitor = gr.Button("新建隧道")
        
        code_visitor = gr.Code(label="观察者参数(格式toml)", interactive=True)
      
        btn_new_visitor.click(
          fn=new_visitor_from_code, 
          inputs=[dp_program_id_new_visitor, code_visitor], 
          show_api=False
          )
      
      with gr.Tab("修改/删除观察者") as change_visitor_tab:
        with gr.Row():
          dp_program_id_change_visitor = gr.Dropdown(interactive=True)
          change_visitor_tab.select(
            fn=get_dp_choices_for_program_name, 
            outputs=dp_program_id_change_visitor, 
            show_api=False
            )

          dp_visitor_name = gr.Dropdown(interactive=True)
          
          def get_dp_choices_for_visitors(pname):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = get_visitors_by_program_id(program_id_name_map[pname])
            if not msg['status'] == '成功':
              logger.error(f"获取观察者数据错误，错误：{msg['message']}")
              raise gr.Error("获取观察者数据错误")
            names = []
            
            for i in msg['data']:
              names.append(i['name'])
            return gr.Dropdown(choices=names, value= names[0] if len(names) > 0 else None)
          dp_program_id_change_visitor.change(
            fn=get_dp_choices_for_visitors, 
            inputs=[dp_program_id_change_visitor], 
            outputs=dp_visitor_name, 
            show_api=False
            )
          
          def get_visitor_config_for_code(pname, name):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = get_visitor_by_name(program_id_name_map[pname], name)
            if not msg['status'] == '成功':
              logger.error(f"获取观察者数据错误，错误：{msg['message']}")
              raise gr.Error("获取观察者数据错误")

            data = toml.dumps(msg['data'])
            
            return gr.Code(data)
          
          def update_visitor_from_code(pname, config):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            data = json.dumps(toml.loads(config), ensure_ascii=False)

            msg = update_visitor_by_name(program_id_name_map[pname], data)
            if not msg['status'] == "成功":
              logger.error(f"更新观察者错误，错误：{msg['message']}")
              raise gr.Error(f"更新观察者错误，错误：{msg['message']}")
            gr.Success(msg['message'])
          
          def del_visitor(pname, name):
            program_list = list_programs()
            if not program_list["status"] == "成功":
              logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
              raise gr.Error("获取程序列表数据错误")
            
            program_id_name_map = {}
            for i in program_list['data']:
              program_id_name_map[i['name']] = str(i['id'])
            
            msg = delete_visitor_by_name(program_id_name_map[pname], name)
            if not msg['status'] == "成功":
              logger.error(f"删除观察者出现错误，错误：{msg['message']}")
              raise gr.Error(f"删除观察者出现错误，错误：{msg['message']}")
            gr.Success(msg['message'])
          
          btn_get_visitor_config = gr.Button("获取观察者配置")
          btn_update_visitor = gr.Button("更新观察者配置", variant='huggingface')
          btn_del_visitor = gr.Button('删除观察者', variant='stop')

        code_visitor_change = gr.Code(interactive=True)
        
        btn_get_visitor_config.click(
          fn=get_visitor_config_for_code, 
          inputs=[dp_program_id_change_visitor, dp_visitor_name], 
          outputs=code_visitor_change,
          show_api=False
          )
        btn_update_visitor.click(
          fn=update_visitor_from_code, 
          inputs = [dp_program_id_change_visitor, code_visitor_change],
          show_api=False
        )
        btn_del_visitor.click(
          fn=del_visitor,
          inputs=[dp_program_id_change_visitor, dp_visitor_name],
          show_api=False
          )
      visitors_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_new_visitor, 
        show_api=False
        )
    
    
    with gr.Tab("客户端配置文件管理") as client_cfg_tab:
      gr.Markdown("## 客户端配置文件管理界面")
      client_cfg_table = gr.Dataframe()

      def get_client_cfg_table():
        with DataBase(os.path.join(data_path, "data.db")) as db:
          try:
            data = db.query_program()
          except Exception as e:
            logger.error(f"查询数据库错误，错误：{e}")
            raise gr.Error("查询数据库错误")
        
        data_pd = pd.DataFrame(columns = ["program id", "program name", "description", "status",  'connect address', 'webserver'])
        if len(data) <= 0:
          data_pd.loc[0] = ["目前没有客户端", "目前没有客户端", "目前没有客户端", "目前没有客户端", "目前没有客户端", "目前没有客户端"]
        pm = ProgramManager()
        for data_item in data:
          # status
          id = str(data_item[0])
          
          frpc_i = pm.get_instance(id)
          if not frpc_i:
            status = "未运行"
          else:
            status = "运行" if frpc_i.is_running() else "未运行"
          
          # ca
          msg = get_client_config_by_id(id)
          serverAddr = None
          port = None
          http_type = "http://"
          if not msg['status'] == "成功":
            logger.warning(f"客户端ID {id} 配置文件读取失败: {msg['message']}")
          else: 
            cfg = msg['data']
            if "serverAddr" in cfg.keys():
              serverAddr = cfg["serverAddr"]
              serverPort = cfg["serverPort"] if "serverPort" in cfg.keys() else 7000
            
            # webserver
            if "webServer" in cfg.keys():
              ws = cfg["webServer"]
              if ws.keys() & ["port", "user", "password"]:
                addr = ws['addr'] if "addr" in ws.keys() else "127.0.0.1"
                port = ws['port']
              if "tls" in ws.keys():
                http_type = "https://"
          
          data_pd.loc[len(data_pd)] = [
            id, 
            data_item[1], 
            data_item[2] if len(data_item[2]) > 0 else "无", 
            status,
            f"{serverAddr}:{serverPort}" if serverAddr else "无", 
            f"{http_type}{addr}:{port}" if port else "无", 
            ]
        
        return gr.Dataframe(value = data_pd)
    
      client_cfg_tab.select(
        fn=get_client_cfg_table,
        outputs=client_cfg_table,
        show_api=False
        )
      # 新建客户端 删除客户端
      # 新建配置文件， 修改删除配置文件
      
      with gr.Tab("客户端操作"):
        with gr.Tab("程序启停控制") as control_tab:
          with gr.Row():
            dp_pid_control = gr.Dropdown(interactive=True)
            control_tab.select(
              show_api=False,
              fn=get_dp_choices_for_program_name,
              outputs=dp_pid_control
            )
            
            with gr.Column():
              btn_control_start = gr.Button("启动", variant="primary")
              btn_control_reload = gr.Button("热重载")
            with gr.Column():
              btn_control_stop = gr.Button("停止", variant="stop")
              btn_control_restart = gr.Button("重启")
            
            async def control(pname, action):
              program_name_ip_map = get_program_name_ip_map()
              
              msg = await program_controller(program_name_ip_map[pname], action)
              if not msg:
                logger.error("操作失败，错误：返回为None")
                raise gr.Error("操作失败")
              if not msg['status'] == '成功':
                logger.error("操作失败，错误：%s" % msg['message'])
                raise gr.Error("操作失败")

              gr.Success(msg['message'])
            
            btn_control_start.click(
              fn=control,
              inputs=[dp_pid_control, gr.State('start')],
              show_api=False
              )

            btn_control_stop.click(
              fn=control,
              inputs=[dp_pid_control, gr.State('stop')],
              show_api=False
              )
            
            btn_control_reload.click(
              fn=control,
              inputs=[dp_pid_control, gr.State('reload')],
              show_api=False
              )
            
            btn_control_restart.click(
              fn=control,
              inputs=[dp_pid_control, gr.State('restart')],
              show_api=False
              )
        with gr.Tab("新建客户端"): 
          new_program()
        with gr.Tab("删除客户端") as client_del_tab: 
          with gr.Row():
            dp_pid_client_del = gr.Dropdown(interactive=True)
            client_del_tab.select(
              fn=get_dp_choices_for_program_name,
              outputs=dp_pid_client_del, 
              show_api=False
            )
            
            def client_del(pname):
              program_name_ip_map = get_program_name_ip_map()
              
              msg = delete_program(program_name_ip_map[pname])
              if not msg['status'] == "成功":
                raise gr.Error(f"删除客户端失败: {msg['message']}")
              gr.Success(msg['message'])
            
            btn_client_del = gr.Button("删除客户端")
            btn_client_del.click(
              show_api=False,
              fn=client_del,
              inputs=dp_pid_client_del
            )
      client_cfg_tab.select(
          show_api=False,
          fn=get_dp_choices_for_program_name,
          outputs=dp_pid_control
        )
      
      with gr.Tab("客户端配置文件操作") as ccfg_action_tab:
        with gr.Tab("修改/删除客户端配置文件") as ccfg_change_tab:
          with gr.Row():
            dp_pid_change_ccfg = gr.Dropdown(interactive=True) # ccfg = client config
            ccfg_change_tab.select(
              show_api=False,
              fn=get_dp_choices_for_program_name,
              outputs=dp_pid_change_ccfg,
            )
            
            def get_client_config_for_code(pname):
              program_list = list_programs()
              if not program_list["status"] == "成功":
                logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
                raise gr.Error("获取程序列表数据错误")
              
              program_id_name_map = {}
              for i in program_list['data']:
                program_id_name_map[i['name']] = str(i['id'])
              
              msg = get_client_config_by_id(program_id_name_map[pname])
              if not msg['status'] == '成功':
                logger.error(f"获取客户端配置文件错误，错误：{msg['message']}")
                raise gr.Error("获取客户端配置文件错误")

              data = toml.dumps(msg['data'])
              
              return gr.Code(data)
            
            def update_client_config_from_code(pname, config):
              program_list = list_programs()
              if not program_list["status"] == "成功":
                logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
                raise gr.Error("获取程序列表数据错误")
              
              program_id_name_map = {}
              for i in program_list['data']:
                program_id_name_map[i['name']] = str(i['id'])
              
              data = json.dumps(toml.loads(config), ensure_ascii=False)

              msg = update_client_config(program_id_name_map[pname], data)
              if not msg['status'] == "成功":
                logger.error(f"更新客户端配置文件错误，错误：{msg['message']}")
                raise gr.Error(f"更新客户端配置文件错误，错误：{msg['message']}")
              gr.Success(msg['message'])
            
            def del_client_config(pname):
              program_list = list_programs()
              if not program_list["status"] == "成功":
                logger.error(f"获取程序列表数据错误，错误：{program_list['message']}")
                raise gr.Error("获取程序列表数据错误")
              
              program_id_name_map = {}
              for i in program_list['data']:
                program_id_name_map[i['name']] = str(i['id'])
              
              msg = delete_client_config(program_id_name_map[pname])
              if not msg['status'] == "成功":
                logger.error(f"删除客户端配置文件出现错误，错误：{msg['message']}")
                raise gr.Error(f"删除客户端配置文件出现错误，错误：{msg['message']}")
              gr.Success(msg['message'])
            
            btn_get_ccfg = gr.Button("获取客户端配置文件")
            btn_update_ccfg = gr.Button("更新客户端配置文件", variant='huggingface')
            btn_del_ccfg = gr.Button('删除客户端配置文件', variant='stop')
          
          code_ccfg_change = gr.Code(interactive=True)
          
          btn_get_ccfg.click(
          fn=get_client_config_for_code, 
          inputs=dp_pid_change_ccfg, 
          outputs=code_ccfg_change,
          show_api=False
          )
          btn_update_ccfg.click(
            fn=update_client_config_from_code, 
            inputs = [dp_pid_change_ccfg, code_ccfg_change],
            show_api=False
          )
          btn_del_ccfg.click(
            fn=del_client_config,
            inputs=dp_pid_change_ccfg,
            show_api=False
            )
          
        with gr.Tab("新建客户端配置文件") as ccfg_new_tab:
          with gr.Row():
            dp_pid_new_cfg = gr.Dropdown(interactive=True)
            ccfg_new_tab.select(
              show_api=False,
              fn=get_dp_choices_for_program_name,
              outputs=dp_pid_new_cfg
            )
            btn_new_ccfg = gr.Button('新建客户端配置文件')
          
          code_ccfg_new = gr.Code(interactive=True)
          
          def new_client_config_from_code(pname, config):
            program_name_ip_map = get_program_name_ip_map()
            
            try:
              data = json.dumps(toml.loads(config), ensure_ascii=False) # TODO：给所有的toml格式转换加try
            except Exception as e:
              logger.error("TOML格式转换失败，错误信息：%s" % str(e))
              raise gr.Error("TOML格式转换失败，错误信息：%s" % str(e))
            
            msg = new_client_config(program_name_ip_map[pname], data)
            if not msg['status'] == "成功":
              logger.error("新建配置文件出错, 错误%s" % msg['message'])
              raise gr.Error("新建配置文件出错")

            gr.Success(msg['message'])
          
          btn_new_ccfg.click(
            show_api=False,
            fn=new_client_config_from_code,
            inputs=[dp_pid_new_cfg, code_ccfg_new]
          )
        
        ccfg_action_tab.select(
          show_api=False,
          fn=get_dp_choices_for_program_name,
          outputs=dp_pid_change_ccfg,
        )
    
    
    with gr.TabItem("日志") as log_tab:
      gr.Markdown("## 查看程序日志")
      
      program_dict = {} # key: name, v: id
      with DataBase(os.path.join(data_path, "data.db")) as db:
        try:
          r = db.query_program()
          for i in r:
            program_dict[i[1]] = str(i[0])
        except Exception as e:
          logger.error(f"数据库操作错误，错误：{e}")
          raise gr.Error("数据库操作错误")
      
      dropdown = gr.Dropdown(
        choices=list(program_dict.keys()),
        label="选择要查看日志的客户端",
        )
      btn = gr.Button("查看")
      # log_text_box = gr.Textbox(label="实时日志输出", interactive=False, max_lines=100)
      gr.Markdown("")
      log_html_box = gr.HTML(
        label="日志输出", 
        max_height=400,
        )

      btn.click(
        fn=watch_log, 
        inputs=[dropdown, gr.State(program_dict)], 
        outputs=log_html_box,
        show_api=False
        )
    
    
    with gr.TabItem("MCP API", id=1) as mcp_tab:
      with gr.Tabs():
        with gr.TabItem("隧道(proxies)配置", id="page2"):
          page_proxies_mcp()
        with gr.TabItem("观察者(visitors)配置", id="page3"):
          page_visitors_mcp()
        with gr.TabItem("客户端配置", id="page4"):
          page_programs_mcp()
        with gr.TabItem("客户端配置文件配置", id="page5"):
          page_client_configs_mcp()


def _cleanup_before_exit(type_: str = ""):
  logger.info(f"收到退出信号{type_}，开始清理工作…")
  program_manager: ProgramManager = ProgramManager()
  program_manager.stop_all()

# 在程序正常退出时也执行一次清理
atexit.register(_cleanup_before_exit)
# 捕获 kill (SIGTERM)
signal.signal(signal.SIGTERM, lambda signum, frame: (_cleanup_before_exit("SIGTERM"), sys.exit(0)))


if __name__ == "__main__":
    # 检测data文件夹存不存在
    if not os.path.exists(data_path):
        os.makedirs(data_path)
        init()
    
    demo.launch(
        mcp_server=True, 
        server_name="0.0.0.0"
    )
