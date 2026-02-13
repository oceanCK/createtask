"""
飞书一键建单 - 主入口程序
提供Web服务接收飞书多维表自动化请求，创建TAPD工单
"""
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import json

from config import get_config, init_config, AppConfig
from webhook_service import FeishuWebhookHandler, TicketService, CreateTicketResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="飞书一键建单服务",
    description="接收飞书多维表自动化HTTP请求，自动在TAPD创建工单",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局处理器实例
webhook_handler: Optional[FeishuWebhookHandler] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global webhook_handler
    
    # 初始化配置
    config = init_config()
    
    # 验证配置
    is_valid, errors = config.validate()
    if not is_valid:
        logger.warning(f"配置不完整: {errors}")
        logger.warning("请配置必要的环境变量或创建 app_config.json 文件")
    
    # 初始化Webhook处理器
    webhook_handler = FeishuWebhookHandler(config)
    
    logger.info("飞书一键建单服务已启动")
    logger.info(f"Webhook 端点: http://0.0.0.0:{config.feishu.webhook_port}/webhook/feishu")


@app.get("/")
async def root():
    """根路径 - 健康检查"""
    return {
        "status": "running",
        "service": "飞书一键建单服务",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    config = get_config()
    is_valid, errors = config.validate()
    
    return {
        "status": "healthy" if is_valid else "degraded",
        "config_valid": is_valid,
        "config_errors": errors if not is_valid else None
    }


@app.post("/webhook/feishu")
async def feishu_webhook(
    request: Request,
    x_lark_request_timestamp: Optional[str] = Header(None),
    x_lark_request_nonce: Optional[str] = Header(None),
    x_lark_signature: Optional[str] = Header(None)
):
    """
    飞书Webhook端点 - 接收飞书多维表自动化请求
    
    请求格式示例：
    ```json
    {
        "ticket_type": "story",  // 或 "bug"
        "标题": "需求标题",
        "描述": "详细描述内容",
        "处理人": "张三",
        "标签类型": "PROGRAM",
        "图片": "https://example.com/image.png"
    }
    ```
    
    或使用嵌套格式：
    ```json
    {
        "ticket_type": "bug",
        "record": {
            "标题": "缺陷标题",
            "描述": "复现步骤...",
            "处理人": "李四",
            "严重程度": "一般"
        }
    }
    ```
    """
    global webhook_handler
    
    if webhook_handler is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        # 获取请求体
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""
        
        logger.info(f"收到飞书原始请求体: {body_str[:1000]}")
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        
        # 尝试解析 JSON
        if not body_str or not body_str.strip():
            logger.warning("请求体为空")
            return JSONResponse(content={"status": "error", "message": "请求体为空"})
        
        try:
            body_json = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 原始内容: {body_str[:500]}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        
        logger.info(f"收到飞书请求: {json.dumps(body_json, ensure_ascii=False)[:500]}")
        
        # 验证请求（可选）
        if x_lark_signature:
            if not webhook_handler.verify_request(
                x_lark_request_timestamp or "",
                x_lark_request_nonce or "",
                x_lark_signature,
                body
            ):
                logger.warning("请求签名验证失败")
                raise HTTPException(status_code=401, detail="签名验证失败")
        
        # 处理请求
        response = webhook_handler.handle_request(body_json)
        
        logger.info(f"处理结果: {json.dumps(response, ensure_ascii=False)[:500]}")
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"处理请求时发生错误: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": -1,
                "message": f"服务器错误: {str(e)}",
                "data": None
            }
        )


@app.post("/api/create/story")
async def create_story(request: Request):
    """
    直接创建需求单API
    
    请求体示例：
    ```json
    {
        "标题": "需求标题",
        "描述": "详细描述",
        "处理人": "张三",
        "标签类型": "PROGRAM"
    }
    ```
    """
    global webhook_handler
    
    if webhook_handler is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        body = await request.json()
        result = webhook_handler.create_ticket('story', body)
        
        if result.success:
            return {
                "status": "success",
                "data": {
                    "id": result.ticket_id,
                    "url": result.ticket_url
                }
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": result.error_message
                }
            )
    except Exception as e:
        logger.exception(f"创建需求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create/bug")
async def create_bug(request: Request):
    """
    直接创建缺陷单API
    
    请求体示例：
    ```json
    {
        "标题": "缺陷标题",
        "描述": "复现步骤...",
        "处理人": "李四",
        "严重程度": "一般"
    }
    ```
    """
    global webhook_handler
    
    if webhook_handler is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        body = await request.json()
        result = webhook_handler.create_ticket('bug', body)
        
        if result.success:
            return {
                "status": "success",
                "data": {
                    "id": result.ticket_id,
                    "url": result.ticket_url
                }
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": result.error_message
                }
            )
    except Exception as e:
        logger.exception(f"创建缺陷失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/check")
async def check_config():
    """检查当前配置状态"""
    config = get_config()
    is_valid, errors = config.validate()
    
    return {
        "valid": is_valid,
        "errors": errors,
        "tapd": {
            "workspace_id": config.tapd.workspace_id,
            "api_user_set": bool(config.tapd.api_user),
            "api_password_set": bool(config.tapd.api_password)
        },
        "feishu": {
            "webhook_port": config.feishu.webhook_port,
            "webhook_path": config.feishu.webhook_path,
            "verification_enabled": bool(config.feishu.verification_token)
        }
    }


@app.get("/api/workitem-types")
async def get_workitem_types():
    """获取需求类别映射配置"""
    config = get_config()
    return {
        "types": config.workitem_types.label_to_type_id
    }


def run_server(host: str = "0.0.0.0", port: int = None, reload: bool = False):
    """运行服务器"""
    config = get_config()
    port = port or config.feishu.webhook_port
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           飞书一键建单服务 - TAPD工单自动化                  ║
╠══════════════════════════════════════════════════════════════╣
║  服务地址: http://{host}:{port}                            
║  Webhook端点: http://{host}:{port}/webhook/feishu          
║  健康检查: http://{host}:{port}/health                     
║  API文档: http://{host}:{port}/docs                        
╠══════════════════════════════════════════════════════════════╣
║  配置状态:                                                   
║    TAPD Workspace: {config.tapd.workspace_id or '未配置'}          
║    API User: {'已配置' if config.tapd.api_user else '未配置'}              
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="飞书一键建单服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务地址")
    parser.add_argument("--port", type=int, default=8080, help="服务端口")
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载）")
    parser.add_argument("--config", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 如果指定了配置文件，先初始化
    if args.config:
        init_config(args.config)
    
    run_server(host=args.host, port=args.port, reload=args.reload)
