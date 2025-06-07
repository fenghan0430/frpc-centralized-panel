import subprocess
import threading
import asyncio
import logging

class FrpcInstance:
    def __init__(self, executable: str, config_path: str, id: str):
        """
        初始化 FRPC 实例。

        Args:
            executable (str): FRPC 可执行文件路径。
            config_path (str): 配置文件路径。
        """
        self.executable = executable
        self.config_path = config_path
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.logger = logging.getLogger("utils.frpc_instance")
        self.id = id

    def start(self):
        """
        启动 FRPC 进程并监控其标准输出与错误输出。

        Raises:
            Exception: 启动进程时发生的异常。
        """
        try:
            self.process = subprocess.Popen(
                [self.executable, '-c', self.config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8'
            )
            self.stdout_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stdout, "STDOUT"),
                daemon=True
            )
            self.stderr_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stderr, "STDERR"),
                daemon=True
            )
            self.stdout_thread.start()
            self.stderr_thread.start()
            self.logger.info(f"FRPC id {self.id} 启动成功 PID: {self.process.pid}")
        except Exception as e:
            self.logger.error(f"FRPC id {self.id} 启动失败: {str(e)}")

    def _read_output(self, pipe, label):
        """
        读取并打印子进程输出。

        Args:
            pipe (io.TextIOWrapper): 子进程的输出管道（stdout 或 stderr）。
            label (str): 输出类型标签（"STDOUT" 或 "STDERR"）。
        """
        while True:
            line = pipe.readline().strip()
            if not line:
                break
            self.logger.info(f"FRPC id {self.id} : {line}")
        pipe.close()
    async def stop(self):
        """
        优雅地异步终止 FRPC 进程。
        如果进程在指定时间内未退出，则强制终止进程。
        """
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # 等待3秒，若未退出则强制终止
                for _ in range(30):
                    if self.process.poll() is not None:
                        break
                    await asyncio.sleep(0.1)
                else:
                    self.process.kill()
                self.logger.info(f"FRPC id {self.id} 已停止")
            except Exception as e:
                self.logger.error(f"FRPC id {self.id} 停止失败: {str(e)}")
                raise e
            finally:
                self.process = None

    def is_running(self):
        """
        检查 FRPC 进程是否正在运行。

        Returns:
            bool: 若进程在运行则为 True，否则为 False。
        """
        return self.process and self.process.poll() is None
