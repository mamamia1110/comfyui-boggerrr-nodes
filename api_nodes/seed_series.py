try:
    from .seed_api_call import request
    from ..utils.image_func import tensor2pil,pil2tensor
except:
    from seed_api_call import request
    from utils.image_func import tensor2pil,pil2tensor

import datetime
import json
import base64
import time
from PIL import Image
import io
import os
import dotenv
dotenv.load_dotenv()

AK = os.getenv("SEED_AK")
SK = os.getenv("SEED_SK")

# Validate environment variables
if not AK or not SK:
    raise Exception("Missing required environment variables: SEED_AK and SEED_SK must be set in .env file")

print(f"AK: {'*' * 8 if AK else 'None'}, SK: {'*' * 8 if SK else 'None'}")

class SeedEdit3:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0x7FFFFFFF, "control_after_generate": True, "tooltip": "随机种子，作为确定扩散初始状态的基础，默认-1（随机）。若随机种子为相同正整数且其他参数均一致，则生成内容极大概率效果一致"}),
                "scale": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,                    "max": 1.0,
                    "step": 0.01,
                    "round": 0.001, #表示舍入精度的值，默认将设置为步长值。可以设置为 False 以禁用舍入。
                    "display": "number",
                    "tooltip": "文本描述影响的程度，该值越大代表文本描述影响程度越大，且输入图片影响程度越小"
                }),
                "prompt": ("STRING", {
                    "multiline": True, #如果您希望字段看起来像 ClipTextEncode 节点上的字段，则为 True
                    "default": "生成一只猫",
                    "tooltip": "用于编辑图像的提示词"
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True, #如果您希望字段看起来像 ClipTextEncode 节点上的字段，则为 True
                    "default": "水印",
                    "tooltip": "不希望在图像中出现的内容"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)

    FUNCTION = "call_jimeng"

    CATEGORY = "🦜Boggerrr_Nodes/api_nodes"

    def call_jimeng(self, image, seed, scale, prompt, negative_prompt):
        # 设置超时时间（秒）
        TIMEOUT_SECONDS = 60  # 60s超时   
        start_time = time.time()
        
        # 将ComfyUI的图像从numpy数组转为image再转为base64
        image = tensor2pil(image)
        
        # 将 PIL Image 转换为 base64 编码
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        now = datetime.datetime.utcnow()
        # 将图像转换为 base64 编码
        binary_string = [image_base64]
        body = {"req_key": "seededit_v3.0", "prompt": prompt, "binary_data_base64": binary_string,"scale":scale,"seed":seed,"negative_prompt":negative_prompt}
        try:
            # 第一次请求：提交任务
            response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncSubmitTask", json.dumps(body))
            print(f"任务提交响应: {response_body['code']}, {response_body['message']}")
            
            # 检查第一次请求是否成功
            if response_body['code'] != 10000:
                raise Exception(f"任务提交失败: {response_body['message']}")
            
            # 获取任务ID
            task_id = response_body['data']['task_id']
            body = {"req_key": "seededit_v3.0", "task_id": task_id}
            
            # 第二次请求：循环查询结果
            while True:
                # 检查是否超时
                current_time = time.time()
                if current_time - start_time > TIMEOUT_SECONDS:
                    raise Exception(f"请求超时：已等待 {TIMEOUT_SECONDS} 秒，任务ID: {task_id}")
                
                try:
                    response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncGetResult", json.dumps(body))
                    
                    if response_body['code'] == 10000:
                        if response_body['data']['status'] == "done":
                            print(f"任务完成: {response_body['data']['status']}")
                            # 解码返回的图像数据
                            img_code = base64.b64decode(response_body['data']['binary_data_base64'][0].replace("\n",""))
                            
                            # 将 bytes 转换为 PIL Image
                            pil_image = Image.open(io.BytesIO(img_code))
                            
                            # 转换为 RGB 模式（如果需要）
                            if pil_image.mode != 'RGB':
                                pil_image = pil_image.convert('RGB')
                            
                            # 使用 pil2tensor 转换为 tensor
                            image_tensor = pil2tensor(pil_image)
                            
                            return (image_tensor,)
                        elif response_body['data']['status'] == "failed":
                            raise Exception(f"任务处理失败: {response_body['data'].get('error_message', '未知错误')}")
                    else:
                        print(f"查询结果响应异常: {response_body['code']}, {response_body['message']}")
                        
                except Exception as e:
                    print(f"查询结果时发生错误: {str(e)}")
                    # 如果是网络错误，继续重试直到超时
                    pass
                    
                time.sleep(1)
                
        except Exception as e:
            error_msg = f"SeedEdit3 请求失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)


class Seedream3:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0x7FFFFFFF, "control_after_generate": True, "tooltip": "随机种子，作为确定扩散初始状态的基础，默认-1（随机）。若随机种子为相同正整数且其他参数均一致，则生成内容极大概率效果一致"}),
                "scale": ("FLOAT", {
                    "default": 2.5,
                    "min": 0.0,                    "max": 10.0,
                    "step": 0.01,
                    "round": 0.001, #表示舍入精度的值，默认将设置为步长值。可以设置为 False 以禁用舍入。
                    "display": "number",
                    "tooltip": "文本描述影响的程度，该值越大代表文本描述影响程度越大，且输入图片影响程度越小"
                }),
                "prompt": ("STRING", {
                    "multiline": True, #如果您希望字段看起来像 ClipTextEncode 节点上的字段，则为 True
                    "default": "生成一只猫",
                    "tooltip": "用于编辑图像的提示词"
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True, #如果您希望字段看起来像 ClipTextEncode 节点上的字段，则为 True
                    "default": "水印",
                    "tooltip": "不希望在图像中出现的内容"
                }),
                "width": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 8, "tooltip": "图像宽度"}),
                "height": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 8, "tooltip": "图像高度"}),
                "beautify_prmopt": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否自动美化提示词"
                })
            },
        }

    RETURN_TYPES = ("IMAGE",)
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "call_jimeng"

    #OUTPUT_NODE = False

    CATEGORY = "🦜Boggerrr_Nodes/api_nodes"

    def call_jimeng(self, seed:int, scale:float, prompt:str, negative_prompt:str, width:int, height:int, beautify_prmopt:bool):
        # 设置超时时间（秒）
        TIMEOUT_SECONDS = 60  # 60秒超时
        start_time = time.time()
        
        now = datetime.datetime.utcnow()

        body = {"req_key": "high_aes_general_v30l_zt2i", "prompt": prompt,"scale":scale,"seed":seed,"width":width,"height":height,"use_pre_llm":beautify_prmopt,"negative_prompt":negative_prompt}
        print(body)
        try:
            # 第一次请求：提交任务
            response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncSubmitTask", json.dumps(body))
            print(response_body)
            print(f"任务提交响应: {response_body['code']}, {response_body['message']}")
            
            # 检查第一次请求是否成功
            if response_body['code'] != 10000:
                raise Exception(f"任务提交失败: {response_body['message']}")
            
            # 获取任务ID
            task_id = response_body['data']['task_id']
            body = {"req_key": "high_aes_general_v30l_zt2i", "task_id": task_id}
            
            # 第二次请求：循环查询结果
            while True:
                # 检查是否超时
                current_time = time.time()
                if current_time - start_time > TIMEOUT_SECONDS:
                    raise Exception(f"请求超时：已等待 {TIMEOUT_SECONDS} 秒，任务ID: {task_id}")
                
                try:
                    response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncGetResult", json.dumps(body))
                    
                    if response_body['code'] == 10000:
                        if response_body['data']['status'] == "done":
                            print(f"任务完成: {response_body['data']['status']}")
                            # 解码返回的图像数据
                            img_code = base64.b64decode(response_body['data']['binary_data_base64'][0].replace("\n",""))
                            
                            # 将 bytes 转换为 PIL Image
                            pil_image = Image.open(io.BytesIO(img_code))
                            
                            # 转换为 RGB 模式（如果需要）
                            if pil_image.mode != 'RGB':
                                pil_image = pil_image.convert('RGB')
                            
                            # 使用 pil2tensor 转换为 tensor
                            image_tensor = pil2tensor(pil_image)
                            
                            return (image_tensor,)
                        elif response_body['data']['status'] == "failed":
                            raise Exception(f"任务处理失败: {response_body['data'].get('error_message', '未知错误')}")
                    else:
                        print(f"查询结果响应异常: {response_body['code']}, {response_body['message']}")
                        
                except Exception as e:
                    print(f"查询结果时发生错误: {str(e)}")
                    # 如果是网络错误，继续重试直到超时
                    pass
                    
                time.sleep(1)
                
        except Exception as e:
            error_msg = f"SeedDream3 请求失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
# 设置 web 目录，该目录中的任何 .js 文件都将被前端作为前端扩展加载
# WEB_DIRECTORY = "./somejs"

NODE_CLASS_MAPPINGS = {
    "SeedEdit3": SeedEdit3,
    "Seedream3": Seedream3
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedEdit3": "SeedEdit3.0",
    "Seedream3": "Seedream3.0"
}


if __name__ == "__main__":
    # Validate environment variables again for testing
    if not AK or not SK:
        raise Exception("Missing required environment variables: SEED_AK and SEED_SK must be set in .env file")
    print(f"Test - AK: {'*' * 8 if AK else 'None'}, SK: {'*' * 8 if SK else 'None'}")