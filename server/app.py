import uvicorn
import os

if __name__ == "__main__":
    # 在生产环境中，建议使用 gunicorn 或类似工具管理 uvicorn
    # 但为了简单起见，这里直接启动
    # host="0.0.0.0" 监听所有网卡
    # port=9000 服务端内部端口，Nginx反代到此端口
    uvicorn.run("src.main:app", host="0.0.0.0", port=9000, reload=False)
