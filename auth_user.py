import asyncio
import os
import sys
import platform
from pyrogram import Client
from app.config.settings import (
    API_ID, API_HASH, SESSION_NAME,
    USE_PROXY, PROXY_TYPE, PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD
)

async def main():
    """用户账号认证 - 生成用于索引历史消息的会话文件"""
    print("\n" + "="*50)
    print("用户账号认证脚本 - 生成会话文件")
    print("="*50)
    
    # 检查API设置
    if not API_ID or not API_HASH:
        print("错误: API_ID 或 API_HASH 未设置。请检查 .env 文件")
        sys.exit(1)
    
    # 设置会话名称
    session_name = SESSION_NAME + "_user"
    
    print(f"使用会话名: {session_name}")
    
    # 关键：生成唯一设备标识，避免挤掉其他会话
    # 使用固定设备标识是安全的，因为不同应用间仍然使用不同的标识
    # 这确保了此应用不会影响其他设备上的Telegram会话
    device_model = f"TgMediaSearchBot"  # 使用固定名称，不包含随机元素
    system_version = platform.system()  # 操作系统类型
    app_version = "1.0.0"
    
    print(f"设备标识: {device_model} ({system_version})")
    
    # 创建客户端 - 关键参数说明:
    # - device_model: 设备标识，避免与其他设备冲突
    # - system_version: 系统版本，帮助区分不同环境
    # - app_version: 应用版本，便于追踪
    # - in_memory=False: 将会话保存到文件，而非内存
    # Telegram允许同一账号在不同设备类型上同时登录，正确设置这些参数
    # 可以确保此客户端被识别为独立设备，不会挤掉其他设备的会话
    app = Client(
        name=session_name,            # 会话名称（文件存储）
        workdir="./",                 # 工作目录（会话文件位置）
        api_id=API_ID,
        api_hash=API_HASH,
        device_model=device_model,    # 设备标识（关键参数）
        system_version=system_version,# 系统版本（辅助区分）
        app_version=app_version,      # 应用版本（辅助区分）
        in_memory=False,              # 使用文件存储会话
        hide_password=True            # 隐藏密码输入
    )
    
    # 如果启用了代理，添加代理配置
    if USE_PROXY:
        proxy = {
            "scheme": PROXY_TYPE,
            "hostname": PROXY_HOST,
            "port": PROXY_PORT
        }
        
        # 如果有用户名和密码，添加到代理配置中
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy["username"] = PROXY_USERNAME
            proxy["password"] = PROXY_PASSWORD
            
        # 更新代理配置
        app.proxy = proxy
        print(f"使用{PROXY_TYPE}代理: {PROXY_HOST}:{PROXY_PORT}")
    
    # 尝试启动客户端
    try:
        print("\n请按提示输入您的Telegram账号信息:")
        print("1. 输入您的Telegram手机号 (带国家代码，例如: +12025550179)")
        print("2. 输入Telegram发送给您的验证码")
        print("3. 如果账号启用了两步验证，需要输入您的密码")
        
        # 调用start()方法会触发登录流程
        # 由于我们设置了适当的设备参数，此登录不会终止其他设备的会话
        await app.start()
        
        # 获取当前用户信息
        me = await app.get_me()
        session_path = os.path.abspath(f"{session_name}.session")
        
        print("\n✅ 认证成功!")
        print(f"已为用户 {me.first_name} (@{me.username}) 创建会话文件")
        print(f"会话文件已保存到: {session_path}")
        print("\n该会话文件将用于让用户客户端获取群组历史消息。")
        print("⚠️ 重要提示:")
        print("1. 确保您的用户账号已加入需要索引的所有群组")
        print("2. 现在您可以运行 'python3 -m app.main' 启动机器人")
        print("3. 此会话不会影响您在其他设备上的登录状态")
    except Exception as e:
        print(f"\n❌ 认证过程中出现错误: {str(e)}")
        print("请检查API凭据和网络连接后重试")
    finally:
        # 安全关闭连接
        # 注意：stop()方法只会关闭当前连接，不会退出其他设备的会话
        if app.is_connected:
            await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n操作被用户取消")
    finally:
        loop.close() 