#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用本地ComfyUI Flux模型生成角色头像
参考林夕头像风格 + 角色人设图
"""
import json
import urllib.request
import urllib.parse
import random
import os
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

def get_image(filename, subfolder, folder_type):
    """获取生成的图片"""
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_URL}/view?{url_values}") as response:
        return response.read()

def create_flux_workflow(prompt_text, seed=None, width=512, height=768):
    """
    创建Flux工作流 (简化版本，不使用参考图)
    """
    if seed is None:
        seed = random.randint(1, 1000000000)

    workflow = {
        # 加载UNET模型 (z_image_bf16)
        "1": {
            "inputs": {
                "unet_name": "z_image_bf16.safetensors",
                "weight_dtype": "default"
            },
            "class_type": "UNETLoader"
        },
        # 加载Dual CLIP
        "2": {
            "inputs": {
                "clip_name1": "clip_l.safetensors",
                "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
                "type": "flux",
                "device": "default"
            },
            "class_type": "DualCLIPLoader"
        },
        # 加载VAE
        "3": {
            "inputs": {
                "vae_name": "ae.safetensors"
            },
            "class_type": "VAELoader"
        },
        # 正面提示词编码
        "4": {
            "inputs": {
                "text": prompt_text,
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        # 负面提示词编码 (Flux通常不需要，但保留)
        "5": {
            "inputs": {
                "text": "",
                "clip": ["2", 0]
            },
            "class_type": "CLIPTextEncode"
        },
        # 空 latent
        "6": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        # KSampler
        "7": {
            "inputs": {
                "seed": seed,
                "steps": 30,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0]
            },
            "class_type": "KSampler"
        },
        # VAE解码
        "8": {
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0]
            },
            "class_type": "VAEDecode"
        },
        # 保存图片
        "9": {
            "inputs": {
                "filename_prefix": "avatar",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        }
    }
    return workflow

def generate_avatar(character_name, prompt_text, output_dir, seed=None):
    """生成角色头像"""
    print(f"\n正在生成 {character_name} 的头像...")
    print(f"使用模型: z_image_bf16.safetensors")

    # 创建工作流
    workflow = create_flux_workflow(
        prompt_text,
        seed,
        width=512,
        height=768
    )

    # 发送生成请求
    try:
        response = queue_prompt(workflow)
        prompt_id = response['prompt_id']
        print(f"任务ID: {prompt_id}")
    except Exception as e:
        print(f"发送生成请求失败: {e}")
        return None

    # 等待生成完成
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(3)
        try:
            history = get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id]['outputs']
                if '9' in outputs:
                    images = outputs['9']['images']
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
        except Exception as e:
            print(f"获取结果时出错: {e}")
            continue

    print(f"[FAIL] {character_name} 头像生成超时")
    return None

if __name__ == "__main__":
    # 路径设置
    output_dir = r"F:\02-项目存档\界行者\characters\images"

    # 陈默的提示词 (参考林夕头像风格 + 人设特征)
    chenmo_prompt = """masterpiece, best quality, 1boy, solo, portrait, anime style, young man, 24 years old,
heterochromia eyes, left eye amber gold, right eye dark brown,
black hair with silver white tips, white streak in bangs, messy hairstyle,
three fine marks under right eye, gentle smile, crescent moon eyes when smiling,
relaxed and optimistic expression,
wear dark gray oversized work jacket, black turtleneck underneath,
outdoor adventurer style, confident pose,
upper body focus, soft lighting, detailed face, high quality,
similar art style to reference, clean background"""

    # 关锋的提示词
    guanfeng_prompt = """masterpiece, best quality, 1boy, solo, portrait, anime style, young man, 28 years old,
long black hair tied in high ponytail, sharp and confident eyes,
elegant warrior appearance, noble bearing,
wear white traditional chinese style coat with black and gold details,
armor elements, Guanyu descendant, martial artist,
serious but elegant expression,
upper body focus, dramatic lighting, detailed face, high quality,
similar art style to reference, clean background"""

    # 生成头像
    print("=" * 60)
    print("使用Z Image (Flux) 模型生成角色头像")
    print("=" * 60)

    chenmo_path = generate_avatar("chenmo", chenmo_prompt, output_dir, seed=42)
    guanfeng_path = generate_avatar("guanfeng", guanfeng_prompt, output_dir, seed=43)

    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)
    if chenmo_path:
        print(f"陈默头像: {chenmo_path}")
    if guanfeng_path:
        print(f"关锋头像: {guanfeng_path}")
