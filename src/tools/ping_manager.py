import subprocess

class PingManager:
    def __init__(self):
        pass

    def ping(self, address, count=4):
        try:
            p = subprocess.Popen(
                ["ping", "-n", str(count), address],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            )
            output, _ = p.communicate()
            return output
        except Exception as e:
            return f"发生错误: {e}"