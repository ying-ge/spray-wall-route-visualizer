import os
import json
import argparse
import requests
import time
from pathlib import Path

def create_ai_route_request(holds_json_path, repo_owner, repo_name, difficulty=None, climber_height=None, github_token=None):
    """
    创建AI定线请求Issue
    
    参数:
    holds_json_path - 岩点坐标JSON文件路径
    repo_owner - GitHub仓库所有者
    repo_name - GitHub仓库名称
    difficulty - 期望的路线难度（可选）
    climber_height - 攀岩者身高（可选）
    github_token - GitHub个人访问令牌（可选）
    
    返回:
    输出模板路径
    """
    # 加载岩点数据
    with open(holds_json_path, 'r', encoding='utf-8') as f:
        holds_data = json.load(f)
    
    # 提取图片名称
    image_name = os.path.basename(holds_json_path).replace('_holds.json', '')
    
    # 准备提交给AI的数据
    request_data = {
        "image_name": image_name,
        "holds": holds_data.get("holds", []),
        "difficulty": difficulty,
        "climber_height": climber_height
    }
    
    # 创建输出目录
    routes_dir = Path("routes")
    routes_dir.mkdir(exist_ok=True)
    
    # 输出文件路径
    output_path = routes_dir / f"{image_name}_ai_route_template.json"
    
    if github_token:
        # 创建一个新的Issue来请求AI定线
        issue_url = create_github_issue(request_data, repo_owner, repo_name, github_token)
        print(f"已创建AI定线请求: {issue_url}")
        print("请等待AI回复，然后将生成的路线配置保存到routes目录。")
    else:
        # 本地模式：直接保存模板
        template_route = {
            "route_name": f"AI设计的路线 - {image_name}",
            "difficulty": difficulty or "待定",
            "description": "这是由AI设计的攀岩路线，基于检测到的岩点位置。",
            "author": "AI路线设计器",
            "date_created": time.strftime("%Y-%m-%d"),
            "circle_color": [0, 255, 0],
            "text_color": [255, 255, 255],
            "arrow_color": [0, 0, 255],
            "holds": [
                # 建议选择6-12个岩点组成有挑战性但可完成的路线
            ],
            "detected_holds": holds_data.get("holds", [])
        }
        
        # 保存模板
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template_route, f, ensure_ascii=False, indent=2)
        
        print(f"已创建路线模板: {output_path}")
        print("请手动完成路线设计或使用GitHub Issues功能请求AI设计。")
    
    return output_path

def create_github_issue(request_data, repo_owner, repo_name, github_token):
    """创建GitHub Issue来请求AI定线"""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    
    # 准备Issue标题和正文
    title = f"AI路线设计请求: {request_data['image_name']}"
    
    # 格式化岩点数据，最多显示前10个
    holds_preview = request_data['holds'][:10]
    if len(request_data['holds']) > 10:
        holds_preview.append({"note": f"... 及其他 {len(request_data['holds']) - 10} 个岩点"})
    
    holds_json = json.dumps(holds_preview, ensure_ascii=False, indent=2)
    
    # 创建Issue正文
    body = f"""## AI路线设计请求

请为我设计一条攀岩路线，基于以下参数:

### 图片名称
{request_data['image_name']}

### 期望难度
{request_data.get('difficulty', '不指定（由AI决定最佳难度）')}

### 攀岩者身高
{request_data.get('climber_height', '不指定')}

### 岩点位置数据（前10个）
```json
{holds_json}

### 请求
请设计一条合理的攀岩路线，选择适当的岩点子集，并按照从下到上的顺序排列。
路线应具有良好的流畅性、适当的难度和明确的动作。

请以JSON格式回复完整的路线配置，格式如下:
```json
{{
  "route_name": "路线名称",
  "difficulty": "难度等级",
  "description": "路线描述",
  "author": "AI路线设计器",
  "date_created": "2025-08-18",
  "circle_color": [0, 255, 0],
  "text_color": [255, 255, 255],
  "arrow_color": [0, 0, 255],
  "holds": [
    {{"x": 100, "y": 800, "description": "起始点"}},
    {{"x": 200, "y": 700, "description": "第二点"}},
    ...
  ]
}}
```
"""
    
    # 发送请求创建Issue
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": title,
        "body": body
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code == 201:
        return response.json()["html_url"]
    else:
        print(f"创建Issue失败: {response.status_code}")
        print(response.text)
        return None

def main():
    parser = argparse.ArgumentParser(description='AI攀岩路线设计器')
    parser.add_argument('--holds', type=str, required=True, help='岩点坐标JSON文件路径')
    parser.add_argument('--owner', type=str, help='GitHub仓库所有者')
    parser.add_argument('--repo', type=str, help='GitHub仓库名称')
    parser.add_argument('--difficulty', type=str, help='期望的路线难度')
    parser.add_argument('--height', type=str, help='攀岩者身高')
    parser.add_argument('--token', type=str, help='GitHub个人访问令牌')
    
    args = parser.parse_args()
    
    create_ai_route_request(args.holds, args.owner, args.repo, args.difficulty, args.height, args.token)

if __name__ == "__main__":
    main()
```

## 修复的关键点

1. 确保 f-string 中的三引号字符串正确闭合
2. 检查花括号的转义（在 f-string 中显示花括号需要使用双花括号 `{{` 和 `}}`）
3. 确保整个 `body` 变量的格式正确

请将这个修复后的代码替换您现有的 `.github/scripts/ai_route_designer.py` 文件，然后重新运行工作流。这应该可以解决当前的语法错误问题。
