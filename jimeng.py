try:
    from .jimeng_api_call import request
    from .imagefunc import tensor2pil,pil2tensor
except:
    from jimeng_api_call import request
    from imagefunc import tensor2pil,pil2tensor


import datetime
import json
import base64
import time
from PIL import Image
import io
import os
import dotenv
dotenv.load_dotenv()

AK = os.getenv("JIMENG_AK")
SK = os.getenv("JIMENG_SK")
print(AK,SK)
class SeedEdit3:
    """

    类方法
    -------------
    INPUT_TYPES (dict):
        告诉主程序节点的输入参数。
    IS_CHANGED:
        可选方法，用于控制节点何时重新执行。

    属性
    ----------
    RETURN_TYPES (`tuple`):
        输出元组中每个元素的类型。
    RETURN_NAMES (`tuple`):
        可选：输出元组中每个输出的名称。
    FUNCTION (`str`):
        入口点方法的名称。例如，如果 `FUNCTION = "execute"` 那么它将运行 Example().execute()
    OUTPUT_NODE ([`bool`]):
        如果此节点是输出节点，从图中输出结果/图像。SaveImage 节点就是一个例子。
        后端会遍历这些输出节点，如果它们的父图正确连接，则尝试执行所有父节点。
        如果不存在则假定为 False。
    CATEGORY (`str`):
        节点在 UI 中应该出现的类别。
    DEPRECATED (`bool`):
        指示节点是否已弃用。弃用的节点在 UI 中默认隐藏，但在使用它们的现有工作流中仍然
        保持功能。
    EXPERIMENTAL (`bool`):
        指示节点是否为实验性。实验性节点在 UI 中标记为如此，可能在未来的版本中
        发生重大变化或被移除。在生产工作流中谨慎使用。
    execute(s) -> tuple || None:
        入口点方法。此方法的名称必须与属性 `FUNCTION` 的值相同。
        例如，如果 `FUNCTION = "execute"` 那么此方法的名称必须是 `execute`，如果 `FUNCTION = "foo"` 那么它必须是 `foo`。
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
            返回一个字典，其中包含所有输入字段的配置。
            某些类型 (string): "MODEL", "VAE", "CLIP", "CONDITIONING", "LATENT", "IMAGE", "INT", "STRING", "FLOAT"。
            输入类型 "INT", "STRING" 或 "FLOAT" 是节点上字段的特殊值。
            类型可以是选择列表。

            返回: `dict`:
                - 键 input_fields_group (`string`): 可以是 required、hidden 或 optional。节点类必须具有 `required` 属性
                - 值 input_fields (`dict`): 包含输入字段配置:
                    * 键 field_name (`string`): 入口点方法参数的名称
                    * 值 field_config (`tuple`):
                        + 第一个值是表示字段类型的字符串或选择列表。
                        + 第二个值是类型 "INT", "STRING" 或 "FLOAT" 的配置。
        """
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
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "call_jimeng"

    #OUTPUT_NODE = False

    CATEGORY = "YuWen_Nodes/api_nodes"

    def call_jimeng(self, image, seed, scale, prompt, negative_prompt):
        # 设置超时时间（秒）
        TIMEOUT_SECONDS = 60  # 1分钟超时   
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

    """
        如果任何输入发生变化，节点将始终重新执行，但
        此方法可用于强制节点在输入未更改时也重新执行。
        您可以让此节点返回数字或字符串。此值将与上次执行节点时返回的值进行比较，
        如果不同，节点将再次执行。
        此方法在核心仓库中用于 LoadImage 节点，其中它们返回图像哈希作为字符串，
        如果图像哈希在执行之间发生变化，LoadImage 节点将再次执行。
    """
    #@classmethod
    #def IS_CHANGED(s, image, string_field, int_field, float_field, print_to_screen):
    #    return ""

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

    CATEGORY = "YuWen_Nodes/api_nodes"

    def call_jimeng(self, seed:int, scale:float, prompt:str, negative_prompt:str, width:int, height:int, beautify_prmopt:bool):
        # 设置超时时间（秒）
        TIMEOUT_SECONDS = 30  # 30秒超时
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

# 如果您有多个节点，映射方式如下：
# NODE_CLASS_MAPPINGS = {
#     "Jimeng_seededit3": Jimeng_seededit3,
#     "Jimeng_text2img": Jimeng_text2img,
#     "Jimeng_img2img": Jimeng_img2img,
#     "AnotherNode": AnotherNodeClass
# }
# 
# NODE_DISPLAY_NAME_MAPPINGS = {
#     "Jimeng_seededit3": "即梦种子编辑3.0",
#     "Jimeng_text2img": "即梦文本转图像", 
#     "Jimeng_img2img": "即梦图像转图像",
#     "AnotherNode": "另一个节点显示名称"
# }

if __name__ == "__main__":
    print(AK,SK)