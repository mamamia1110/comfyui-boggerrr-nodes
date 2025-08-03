#!/usr/bin/env python3
# coding:utf-8
import datetime
import hashlib
import hmac
import time
import json
import sys
from urllib.parse import quote
import base64
import requests
import os
import dotenv
dotenv.load_dotenv()

# 以下参数视服务不同而不同，一个服务内通常是一致的
Service = "cv"
Version = "2022-08-31"
Region = "cn-north-1"
Host = "visual.volcengineapi.com" 
ContentType = "application/json" 

def norm_query(params):
    query = ""
    for key in sorted(params.keys()):
        if type(params[key]) == list:
            for k in params[key]:
                query = (
                        query + quote(key, safe="-_.~") + "=" + quote(k, safe="-_.~") + "&"
                )
        else:
            query = (query + quote(key, safe="-_.~") + "=" + quote(params[key], safe="-_.~") + "&")
    query = query[:-1]
    return query.replace("+", "%20")


# 第一步：准备辅助函数。
# sha256 非对称加密
def hmac_sha256(key: bytes, content: str):
    return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()


# sha256 hash算法
def hash_sha256(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# 第二步：签名请求函数
def request(method, date, query, header, ak, sk, action, body):
    # 第三步：创建身份证明。其中的 Service 和 Region 字段是固定的。ak 和 sk 分别代表
    # AccessKeyID 和 SecretAccessKey。同时需要初始化签名结构体。一些签名计算时需要的属性也在这里处理。
    # 初始化身份证明结构体
    credential = {
        "access_key_id": ak,
        "secret_access_key": sk,
        "service": Service,
        "region": Region,
    }
    # 初始化签名结构体
    request_param = {
        "body": body,
        "host": Host,
        "path": "/",
        "method": method,
        "content_type": ContentType,
        "date": date,
        "query": {"Action": action, "Version": Version},
    }
    if body is None:
        request_param["body"] = body 
    # 第四步：接下来开始计算签名。在计算签名前，先准备好用于接收签算结果的 signResult 变量，并设置一些参数。
    # 初始化签名结果的结构体
    x_date = request_param["date"].strftime("%Y%m%dT%H%M%SZ")
    short_x_date = x_date[:8]
    x_content_sha256 = hash_sha256(request_param["body"])
    sign_result = {
        "Host": request_param["host"],
        "X-Content-Sha256": x_content_sha256,
        "X-Date": x_date,
        "Content-Type": request_param["content_type"],
    }
    # 第五步：计算 Signature 签名。
    signed_headers_str = ";".join(
        ["content-type", "host", "x-content-sha256", "x-date"]
    )
    #signed_headers_str = signed_headers_str + ";x-security-token"
    canonical_request_str = "\n".join(
        [request_param["method"].upper(),
         request_param["path"],
         norm_query(request_param["query"]),
         "\n".join(
             [
                 "content-type:" + request_param["content_type"],
                 "host:" + request_param["host"],
                 "x-content-sha256:" + x_content_sha256,
                 "x-date:" + x_date,
             ]
         ),
         "",
         signed_headers_str,
         x_content_sha256,
         ]
    )

    # 打印正规化的请求用于调试比对
    #print(canonical_request_str)
    hashed_canonical_request = hash_sha256(canonical_request_str)

    # 打印hash值用于调试比对
    #print(hashed_canonical_request)
    credential_scope = "/".join([short_x_date, credential["region"], credential["service"], "request"])
    string_to_sign = "\n".join(["HMAC-SHA256", x_date, credential_scope, hashed_canonical_request])

    # 打印最终计算的签名字符串用于调试比对
    #print(string_to_sign)
    k_date = hmac_sha256(credential["secret_access_key"].encode("utf-8"), short_x_date)
    k_region = hmac_sha256(k_date, credential["region"])
    k_service = hmac_sha256(k_region, credential["service"])
    k_signing = hmac_sha256(k_service, "request")
    signature = hmac_sha256(k_signing, string_to_sign).hex()

    sign_result["Authorization"] = "HMAC-SHA256 Credential={}, SignedHeaders={}, Signature={}".format(
        credential["access_key_id"] + "/" + credential_scope,
        signed_headers_str,
        signature,
    )
    header = {**header, **sign_result}
    #print(header)
    # header = {**header, **{"X-Security-Token": SessionToken}}
    # 第六步：将 Signature 签名写入 HTTP Header 中，并发送 HTTP 请求。
    r = requests.request(method=method,
                         url="https://{}{}".format(request_param["host"], request_param["path"]),
                         headers=header,
                         params=request_param["query"],
                         data=request_param["body"],
                         )
    
    # 检查HTTP响应状态
    if r.status_code != 200:
        raise Exception(f"API请求失败，HTTP状态码: {r.status_code}, 响应内容: {r.text}")
    
    # 尝试解析JSON响应
    try:
        return r.json()
    except ValueError as e:
        raise Exception(f"API响应不是有效的JSON格式，响应内容: {r.text}, 错误: {str(e)}")


if __name__ == "__main__":
    
    # 获取环境变量
    AK = os.getenv("SEED_AK")
    SK = os.getenv("SEED_SK")
    
    # 验证环境变量
    if not AK or not SK:
        raise Exception("Missing required environment variables: SEED_AK and SEED_SK must be set in .env file")
    
    now = datetime.datetime.utcnow()
    desc = sys.argv[1]
    with open("./img/test.png", 'rb') as f:
        ff = f.read()
    binary_string = [base64.b64encode(ff).decode('utf-8')]
    
    prompt = desc
    body = {"req_key": "seededit_v3.0", "prompt": prompt, "binary_data_base64": binary_string} 
    response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncSubmitTask", json.dumps(body))
    print(response_body['code'],response_body['message'])
    body = {"req_key": "seededit_v3.0", "task_id": response_body['data']['task_id']}
    while True:
        response_body = request("POST", now, {},{}, AK, SK, "CVSync2AsyncGetResult", json.dumps(body))
        if response_body['code'] == 10000:
            if response_body['data']['status'] == "done":
                print(response_body['data']['status'])
                break
        time.sleep(1)

    img_code = base64.b64decode(response_body['data']['binary_data_base64'][0].replace("\n",""))
    path = "./out/result.png"
    with open(path, 'wb') as f:
        f.write(img_code)
