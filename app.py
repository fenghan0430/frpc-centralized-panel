import atexit
import json
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
program_manager = ProgramManager()

def page_client_configs_mcp():
    gr.Markdown("# setting client configs")
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
    gr.Markdown("# visitors mcp tools")

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
    gr.Markdown("# client program")
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
    logger.info("初始化数据库")
    with DataBase(os.path.join(data_path, "data.db")) as db:
        db.init_db()

def page_proxies(tab_var):
  gr.Markdown("## Proxies Management")
  data_table = gr.Dataframe()
  def get_proxies_table():
    data = get_all_proxies()
    if not data["status"] == "成功":
      logger.error(f"Error in obtaining the program list data, Error:{data['message']}")
      raise gr.Error("Error in obtaining the program list data")
    
    program_list = list_programs()
    if not program_list["status"] == "成功":
      logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
      raise gr.Error("Error in obtaining the program list data")
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
      data_pd.loc[0] = ["No Data", "No Data", "No Data", "No Data", "No Data"]

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
  
  tab_var.select(fn=get_proxies_table, outputs=data_table, show_api=False)
  
  with gr.Tab("new tunnel") as new_proxy_tab:
    with gr.Row():
      dp_program_id_new = gr.Dropdown(interactive=True)

      new_proxy_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_new, 
        show_api=False
        ) # TODO: 检查监听
      
      def new_proxy_from_code(pname, toml_str):
        try:
          data = json.dumps(toml.loads(toml_str), ensure_ascii=False)
        except Exception as e:
          logger.error("TOML format conversion failed, error message:%s" % str(e))
          raise gr.Error("TOML format conversion failed, error message:%s" % str(e))

        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = new_proxy(program_id_name_map[pname], data)
        if msg['status'] == '成功':
          gr.Success(msg['message'])
        else:
          raise gr.Error(msg['message'])
      btn_new = gr.Button("new tunnel")
    
    code = gr.Code(label="Tunnel Parameters (TOML Format)", interactive=True)
    btn_new.click(fn=new_proxy_from_code, inputs=[dp_program_id_new, code], show_api=False)
  
  with gr.Tab("Edit/Delete Tunnel") as change_proxy_tab:
    with gr.Row():
      dp_program_id_change = gr.Dropdown(interactive=True)
      change_proxy_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_change, 
        show_api=False
        )
      
      dp_proxy_name = gr.Dropdown(interactive=True)
      
      def get_dp_choices_for_proxies(pname):
        if not pname:
          return gr.Dropdown(choices=[], value=None)
        
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = get_proxy_by_program_id(program_id_name_map[pname])
        if not msg['status'] == '成功':
          logger.error(f"Error fetching proxy data:{msg['message']}")
          raise gr.Error("Error fetching proxy data")
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
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = get_proxy_by_name(program_id_name_map[pname], name)
        if not msg['status'] == '成功':
          logger.error(f"Error in obtaining the program list data, Error:{msg['message']}")
          raise gr.Error("Error in obtaining the program list data")

        data = toml.dumps(msg['data'])
        
        return gr.Code(data)
        
      def update_proxy_from_code(pname, config):
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error fetching program list data: {program_list['message']}")
          raise gr.Error("Error fetching program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        try:
          data = json.dumps(toml.loads(config), ensure_ascii=False)
        except Exception as e:
          logger.error("TOML format conversion failed, error message:%s" % str(e))
          raise gr.Error("TOML format conversion failed, error message:%s" % str(e))

        msg = update_proxy_by_name(program_id_name_map[pname], data)
        if not msg['status'] == "成功":
          logger.error(f"Error updating tunnel configuration data: {msg['message']}")
          raise gr.Error(f"Error updating tunnel configuration data: {msg['message']}")
        gr.Success(msg['message'])
      
      def del_proxy(pname, name):
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = delete_proxy_by_name(program_id_name_map[pname], name)
        if not msg['status'] == "成功":
          logger.error(f"Error deleting tunnel:{msg['message']}")
          raise gr.Error(f"Error deleting tunnel:{msg['message']}")
        gr.Success(msg['message'])
      
      btn_get_proxy_config = gr.Button("Get Tunnel Configuration")
      btn_update_proxy = gr.Button("Update Tunnel Configuration", variant='huggingface')
      btn_del_proxy = gr.Button('Delete Tunnel', variant='stop')
    
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
  
    change_proxy_tab.select(
      fn=get_dp_choices_for_program_name, 
      outputs=dp_program_id_new, 
      show_api=False
      )

def page_visitors(tab_var):
  gr.Markdown("## Visitors Management")
  visitors_data_table = gr.Dataframe()
  def get_visitors_table():
    data = get_all_visitors()
    if not data["status"] == "成功":
      logger.error(f"Error fetching visitor data:{data['message']}")
      raise gr.Error("Error fetching visitor data")
    
    program_list = list_programs()
    if not program_list["status"] == "成功":
      logger.error(f"Error fetching program list data:{program_list['message']}")
      raise gr.Error("Error fetching program list data")
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
      data_pd.loc[0] = ["No Data", "No Data", "No Data", "No Data"]
    for data_item in data:
      route = f"{data_item['serverName']} -> {data_item['bindAddr']}:{data_item['bindPort']}"
      data_pd.loc[len(data_pd)] = [program_id_name_map[str(data_item['program_id'])], data_item['name'], data_item['type'], route]
    
    return gr.Dataframe(value = data_pd)
  
  tab_var.select(fn=get_visitors_table, outputs=visitors_data_table, show_api=False)

  with gr.Tab("New Visitor") as new_visitor_tab:
    with gr.Row():
      dp_program_id_new_visitor = gr.Dropdown(interactive=True)
      new_visitor_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_new_visitor, 
        show_api=False
        )
      
      def new_visitor_from_code(pname, toml_str):
        try:
          cfg = toml.loads(toml_str)
        except Exception as e:
          logger.error("TOML format conversion failed, error message:%s" % str(e))
          raise gr.Error("TOML format conversion failed, error message:%s" % str(e))
        cfg = json.dumps(cfg, ensure_ascii=False)
        
        program_name_id_map = get_program_name_ip_map()
        
        msg = new_visitor(program_name_id_map[pname], cfg)
        if msg['status'] == '成功':
          gr.Success(msg['message'])
        else:
          raise gr.Error(msg['message'])
      
      btn_new_visitor = gr.Button("Create Visitor")
    
    code_visitor = gr.Code(label="Visitor Parameters (TOML Format)", interactive=True)
  
    btn_new_visitor.click(
      fn=new_visitor_from_code, 
      inputs=[dp_program_id_new_visitor, code_visitor], 
      show_api=False
      )
  
  with gr.Tab("Edit/Delete Visitor") as change_visitor_tab:
    with gr.Row():
      dp_program_id_change_visitor = gr.Dropdown(interactive=True)
      change_visitor_tab.select(
        fn=get_dp_choices_for_program_name, 
        outputs=dp_program_id_change_visitor, 
        show_api=False
        )

      dp_visitor_name = gr.Dropdown(interactive=True)
      
      def get_dp_choices_for_visitors(pname):
        if not pname:
          return gr.Dropdown(
            choices=[],
            value=None
          )
        
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = get_visitors_by_program_id(program_id_name_map[pname])
        if not msg['status'] == '成功':
          logger.error(f"Error fetching visitor data: {msg['message']}")
          raise gr.Error("Error fetching visitor data")
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
          logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
          raise gr.Error("Error in obtaining the program list data, Error:")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = get_visitor_by_name(program_id_name_map[pname], name)
        if not msg['status'] == '成功':
          logger.error(f"Error fetching visitor data: {msg['message']}")
          raise gr.Error("Error fetching visitor data")

        data = toml.dumps(msg['data'])
        
        return gr.Code(data)
      
      def update_visitor_from_code(pname, config):
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error fetching program list data: {program_list['message']}")
          raise gr.Error("Error fetching program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        try:
          data = json.dumps(toml.loads(config), ensure_ascii=False)
        except Exception as e:
          logger.error("TOML format conversion failed, error message:%s" % str(e))
          raise gr.Error("TOML format conversion failed, error message:%s" % str(e))

        msg = update_visitor_by_name(program_id_name_map[pname], data)
        if not msg['status'] == "成功":
          logger.error(f"Error updating visitor: {msg['message']}")
          raise gr.Error(f"Error updating visitor: {msg['message']}")
        gr.Success(msg['message'])
      
      def del_visitor(pname, name):
        program_list = list_programs()
        if not program_list["status"] == "成功":
          logger.error(f"Error fetching program list data:{program_list['message']}")
          raise gr.Error("Error fetching program list data")
        
        program_id_name_map = {}
        for i in program_list['data']:
          program_id_name_map[i['name']] = str(i['id'])
        
        msg = delete_visitor_by_name(program_id_name_map[pname], name)
        if not msg['status'] == "成功":
          logger.error(f"Error deleting visitor: {msg['message']}")
          raise gr.Error(f"Error deleting visitor: {msg['message']}")
        gr.Success(msg['message'])
      
      btn_get_visitor_config = gr.Button("Get Visitor Configuration")
      btn_update_visitor = gr.Button("Update Visitor Configuration", variant='huggingface')
      btn_del_visitor = gr.Button('Delete Visitor', variant='stop')

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
  tab_var.select(
    fn=get_dp_choices_for_program_name, 
    outputs=dp_program_id_new_visitor, 
    show_api=False
    )

def page_programs(tab_var):
  gr.Markdown("## Client Management")
  client_cfg_table = gr.Dataframe()

  def get_client_cfg_table():
    with DataBase(os.path.join(data_path, "data.db")) as db:
      try:
        data = db.query_program()
      except Exception as e:
        logger.error(f"Error querying database:{e}")
        raise gr.Error("Error querying database")
    
    data_pd = pd.DataFrame(columns = ["program id", "program name", "description", "status",  'connect address', 'webserver'])
    if len(data) <= 0:
      data_pd.loc[0] = ["No Data", "No Data", "No Data", "No Data", "No Data", "No Data"]
    
    for data_item in data:
      # status
      id = str(data_item[0])
      
      frpc_i = program_manager.get_instance(id)
      if not frpc_i:
        status = "never run"
      else:
        status = "running" if frpc_i.is_running() else "stop"
      
      # ca
      msg = get_client_config_by_id(id)
      serverAddr = None
      port = None
      http_type = "http://"
      if not msg['status'] == "成功":
        logger.warning(f"client ID:{id}failed to read configuration file: {msg['message']}")
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

  tab_var.select(
    fn=get_client_cfg_table,
    outputs=client_cfg_table,
    show_api=False
    )
  # 新建客户端 删除客户端
  # 新建配置文件， 修改删除配置文件
  
  with gr.Tab("Client Actions"):
    with gr.Tab("Actions(start, stop)") as control_tab:
      with gr.Row():
        dp_pid_control = gr.Dropdown(interactive=True)
        control_tab.select(
          show_api=False,
          fn=get_dp_choices_for_program_name,
          outputs=dp_pid_control
        )
        
        with gr.Column():
          btn_control_start = gr.Button("Start", variant="primary")
          btn_control_reload = gr.Button("Reload Config")
        with gr.Column():
          btn_control_stop = gr.Button("Stop", variant="stop")
          btn_control_restart = gr.Button("Restart")
        
        async def control(pname, action):
          program_name_ip_map = get_program_name_ip_map()
          
          msg = await program_controller(program_name_ip_map[pname], action)
          if not msg:
            logger.error("Operation failed, error: returned None")
            raise gr.Error("Operation failed")
          if not msg['status'] == '成功':
            logger.error("Operation failed：%s" % msg['message'])
            raise gr.Error("Operation failed")

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
    with gr.Tab("New Client"): 
      new_program()
    with gr.Tab("Delete Client") as client_del_tab: 
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
            raise gr.Error(f"Failed to delete client:{msg['message']}")
          gr.Success(msg['message'])
        
        btn_client_del = gr.Button("Delete")
        btn_client_del.click(
          show_api=False,
          fn=client_del,
          inputs=dp_pid_client_del
        )
  tab_var.select(
      show_api=False,
      fn=get_dp_choices_for_program_name,
      outputs=dp_pid_control
    )
  
  with gr.Tab("Client Configuration") as ccfg_action_tab:
    with gr.Tab("Edit/Delete Client Configuration File") as ccfg_change_tab:
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
            logger.error(f"Error fetching program list data:{program_list['message']}")
            raise gr.Error("Error fetching program list data")
          
          program_id_name_map = {}
          for i in program_list['data']:
            program_id_name_map[i['name']] = str(i['id'])
          
          msg = get_client_config_by_id(program_id_name_map[pname])
          if not msg['status'] == '成功':
            logger.error(f"Error fetching client configuration file: {msg['message']}")
            raise gr.Error("Error fetching client configuration file")

          data = toml.dumps(msg['data'])
          
          return gr.Code(data)
        
        def update_client_config_from_code(pname, config):
          program_list = list_programs()
          if not program_list["status"] == "成功":
            logger.error(f"Error fetching program list data:{program_list['message']}")
            raise gr.Error("Error fetching program list data")
          
          program_id_name_map = {}
          for i in program_list['data']:
            program_id_name_map[i['name']] = str(i['id'])
          
          try:
            data = json.dumps(toml.loads(config), ensure_ascii=False)
          except Exception as e:
            logger.error("TOML format conversion failed, error message:%s" % str(e))
            raise gr.Error("TOML format conversion failed, error message:%s" % str(e))

          msg = update_client_config(program_id_name_map[pname], data)
          if not msg['status'] == "成功":
            logger.error(f"Error updating client configuration file:{msg['message']}")
            raise gr.Error(f"Error updating client configuration file:{msg['message']}")
          gr.Success(msg['message'])
        
        def del_client_config(pname):
          program_list = list_programs()
          if not program_list["status"] == "成功":
            logger.error(f"Error fetching program list data: {program_list['message']}")
            raise gr.Error("Error fetching program list data: ")
          
          program_id_name_map = {}
          for i in program_list['data']:
            program_id_name_map[i['name']] = str(i['id'])
          
          msg = delete_client_config(program_id_name_map[pname])
          if not msg['status'] == "成功":
            logger.error(f"Error deleting client configuration file: {msg['message']}")
            raise gr.Error(f"Error deleting client configuration file: {msg['message']}")
          gr.Success(msg['message'])
        
        btn_get_ccfg = gr.Button("Get Client Configuration")
        btn_update_ccfg = gr.Button("Update Client Configuration", variant='huggingface')
        btn_del_ccfg = gr.Button('Delete Client Configuration', variant='stop')
      
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
      
    with gr.Tab("New Client Configuration") as ccfg_new_tab:
      with gr.Row():
        dp_pid_new_cfg = gr.Dropdown(interactive=True)
        ccfg_new_tab.select(
          show_api=False,
          fn=get_dp_choices_for_program_name,
          outputs=dp_pid_new_cfg
        )
        btn_new_ccfg = gr.Button('Create Client Configuration')
      
      code_ccfg_new = gr.Code(interactive=True)
      
      def new_client_config_from_code(pname, config):
        program_name_ip_map = get_program_name_ip_map()
        
        try:
          data = json.dumps(toml.loads(config), ensure_ascii=False)
        except Exception as e:
          logger.error("TOML format conversion failed, error message:%s" % str(e))
          raise gr.Error("TOML format conversion failed, error message:%s" % str(e))
        
        msg = new_client_config(program_name_ip_map[pname], data)
        if not msg['status'] == "成功":
          logger.error("Failed to create configuration file, error:%s" % msg['message'])
          raise gr.Error("Failed to create configuration file")

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

def page_logs(tab_var):
  gr.Markdown("## program log")
      
  dropdown = gr.Dropdown(
    choices=[],
    label="Select Client to View Logs",
    )
  
  def log_pid():
    program_dict = {} # key: name, v: id
    with DataBase(os.path.join(data_path, "data.db")) as db:
      try:
        r = db.query_program()
        for i in r:
          program_dict[i[1]] = str(i[0])
      except Exception as e:
        logger.error(f"Database operation error:{e}")
        raise gr.Error("Database operation error")
      return gr.Dropdown(
        choices=list(program_dict.keys()), 
        value = list(program_dict.keys())[0] if len(program_dict.keys()) > 0 else None,
        )
  
  tab_var.select(
    show_api=False,
    fn=log_pid,
    outputs=dropdown
  )
  
  btn = gr.Button("Watch Log")
  # log_text_box = gr.Textbox(label="实时日志输出", interactive=False, max_lines=100)
  gr.Markdown("")
  log_html_box = gr.HTML(
    label="Log", 
    max_height=400,
    )

  btn.click(
    fn=watch_log, 
    inputs=[dropdown], 
    outputs=log_html_box,
    show_api=False
    )

def get_dp_choices_for_program_name():
  program_list = list_programs()
  if not program_list["status"] == "成功":
    logger.error(f"Error in obtaining the program list data, Error message: {program_list['message']}")
    raise gr.Error("Error in obtaining the program list data")
  
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
    logger.error(f"Error in obtaining the program list data, Error:{program_list['message']}")
    raise gr.Error("Error in obtaining the program list data")
  program_list = program_list['data'] # list
  
  program_id_name_map = {}
  for i in range(len(program_list)):
    program_id_name_map[program_list[i]['name']] = str(program_list[i]['id'])
  return program_id_name_map

with gr.Blocks(title="frpc centralized panel") as demo:
  gr.Markdown("# frpc centralized panel with MCP")

  with gr.Tabs():
    
    
    with gr.TabItem("README") as readme_tab:
      with open("./README.md", "r", encoding='utf-8') as f:
        
        gr.Markdown(f.read())
    
    
    with gr.Tab("Proxies Management") as proxies_tab:
      page_proxies(proxies_tab)
  
    with gr.Tab("Visitors Management") as visitors_tab:
      page_visitors(visitors_tab)
    
    with gr.Tab("Client Management") as client_cfg_tab:
      page_programs(client_cfg_tab)
    
    with gr.TabItem("Log") as log_tab:
      page_logs(log_tab)
    
    with gr.TabItem("MCP API", id=1) as mcp_tab:
      with gr.Tabs():
        with gr.TabItem("proxies", id="page2"):
          page_proxies_mcp()
        with gr.TabItem("visitors", id="page3"):
          page_visitors_mcp()
        with gr.TabItem("programs", id="page4"):
          page_programs_mcp()
        with gr.TabItem("client configs", id="page5"):
          page_client_configs_mcp()


def _cleanup_before_exit(type_: str = ""):
  logger.info(f"收到退出信号{type_}，开始清理工作…")
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
    elif not os.path.exists(os.path.join(data_path, "data.db")):
      init()
    
    demo.launch(
        mcp_server=True, 
        server_name="0.0.0.0"
    )
