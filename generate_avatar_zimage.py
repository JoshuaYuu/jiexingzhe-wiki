#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用本地ComfyUI Z Image模型生成角色头像
参考林夕头像风格 + 角色人设图
"""
import json
import urllib.request
import urllib.parse
import random
import os
import base64
import time

COMFYUI_URL = "http://127.0.0.1:8188"

def queue_prompt(prompt):
    """发送生成请求到ComfyUI"""
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    """获取生成历史"""
    with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as response:
        return json.loads(response.read())

def upload_image(image_path, name):
    """上传图片到ComfyUI"""
    with open(image_path, 'rb') as f:
        image_data = f.read()

    import io
    import mimetypes
    boundary = '----WebKitFormBoundary' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))

    body = io.BytesIO()
    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode())
    body.write(b'Content-Type: image/png\r\n\r\n')
    body.write(image_data)
    body.write(f'\r\n--{boundary}--\r\n'.encode())

    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image",
        data=body.getvalue(),
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())
    except Exception as e:
        print(f"上传图片失败: {e}")
        return None

def get_image(filename, subfolder, folder_type):
    """获取生成的图片"""
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{url_values}") as response:
        return response.read()

def create_zimage_workflow(prompt_text, reference_image_name, character_image_name, seed=None, width=512, height=768):
    """
    创建Z Image工作流
    使用TextEncodeZImageOmni节点结合参考图生成头像
    """
    if seed is None:
        seed = random.randint(1, 1000000000)

    workflow = {
        "1": {
            "inputs": {
                "ckpt_name": "z_image_bf16.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text": prompt_text,
                "clip": ["1", 1],
                "auto_resize_images": True,
                "image1": ["10", 0],
                "image2": ["11", 0]
            },
            "class_type": "TextEncodeZImageOmni"
        },
        "3": {
            "inputs": {
                "text": "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, bad feet, mutation, deformed, extra limbs, extra arms, extra legs, malformed limbs, fused fingers, too many fingers, long neck, cross-eyed, mutated hands, polar lowres, bad face, out of frame, oversaturated, overexposure",
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "seed": seed,
                "steps": 30,
                "cfg": 7.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "samples": ["4", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecode"
        },
        "7": {
            "inputs": {
                "filename_prefix": "avatar",
                "images": ["6", 0]
            },
            "class_type": "SaveImage"
        },
        "10": {
            "inputs": {
                "image": reference_image_name
            },
            "class_type": "LoadImage"
        },
        "11": {
            "inputs": {
                "image": character_image_name
            },
            "class_type": "LoadImage"
        }
    }
    return workflow

def generate_avatar_with_reference(character_name, prompt_text, output_dir,
                                   reference_image_path, character_image_path,
                                   seed=None):
    """使用参考图生成角色头像"""
    print(f"\n正在生成 {character_name} 的头像...")
    print(f"提示词: {prompt_text[:100]}...")

    # 上传参考图片
    ref_name = f"ref_{character_name}.png"
    char_name = f"char_{character_name}.png"

    print(f"上传参考图: {reference_image_path}")
    upload_result1 = upload_image(reference_image_path, ref_name)
    if not upload_result1:
        print("上传参考图失败")
        return None

    print(f"上传人设图: {character_image_path}")
    upload_result2 = upload_image(character_image_path, char_name)
    if not upload_result2:
        print("上传人设图失败")
        return None

    # 创建工作流
    workflow = create_zimage_workflow(
        prompt_text,
        ref_name,
        char_name,
        seed,
        width=512,
        height=768
    )

    # 发送生成请求
    response = queue_prompt(workflow)
    prompt_id = response['prompt_id']
    print(f"任务ID: {prompt_id}")

    # 等待生成完成
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(3)
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id]['outputs']
            if '7' in outputs:
                images = outputs['7']['images']
                if images:
                    filename = images[0]['filename']
                    subfolder = images[0]['subfolder']
                    folder_type = images[0]['type']

                    # 获取图片数据
                    image_data = get_image(filename, subfolder, folder_type)

                    # 保存图片
                    output_path = os.path.join(output_dir, f"{character_name}_avatar_v2.png")
                    with open(output_path, 'wb') as f:
                        f.write(image_data)

                    print(f"[OK] {character_name} 头像已保存到: {output_path}")
                    return output_path

    print(f"[FAIL] {character_name} 头像生成超时")
    return None

if __name__ == "__main__":
    # 路径设置
    output_dir = r"F:\02-项目存档\界行者\characters\images"
    linxi_avatar = r"F:\02-项目存档\界行者\characters\images\linxi\avatar.png"
    chenmo_ref = r"F:\02-项目存档\界行者\characters\images\chenmo\Gemini_Generated_Image_8vvn678vvn678vvn.png"
    guanfeng_ref = r"F:\02-项目存档\界行者\characters\images\guanfeng\Gemini_Generated_Image_59pycu59pycu59py.png"

    # 陈默的提示词
    chenmo_prompt = """masterpiece, best quality, 1boy, solo, portrait, young man, 24 years old, 181cm tall, slender build,
heterochromia, left eye amber gold, right eye dark brown, black hair with silver white tips, white streak in bangs,
three fine marks under right eye, gentle smile, crescent moon eyes, relaxed expression,
wear oversized dark gray work jacket, black turtleneck, tactical cargo pants,
outdoor style, adventurer vibe, confident pose,
upper body focus, soft lighting, detailed face, high quality, anime style"""

    # 关锋的提示词
    guanfeng_prompt = """masterpiece, best quality, 1boy, solo, portrait, young man, 28 years old, 185cm tall, muscular build,
long black hair tied in high ponytail, sharp eyes, confident expression, elegant warrior,
wear traditional chinese style coat, black and gold color scheme, armor elements,
Guanyu descendant, martial artist, noble bearing,
upper body focus, dramatic lighting, detailed face, high quality, anime style"""

    # 生成头像
    print("=" * 60)
    print("使用Z Image模型生成角色头像")
    print("参考: 林夕头像风格 + 角色人设图")
    print("=" * 60)

    chenmo_path = generate_avatar_with_reference(
        "chenmo", chenmo_prompt, output_dir,
        linxi_avatar, chenmo_ref, seed=42
    )

    guanfeng_path = generate_avatar_with_reference(
        "guanfeng", guanfeng_prompt, output_dir,
        linxi_avatar, guanfeng_ref, seed=43
    )

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)
    if chenmo_path:
        print(f"陈默头像: {chenmo_path}")
    if guanfeng_path:
        print(f"关锋头像: {guanfeng_path}")
