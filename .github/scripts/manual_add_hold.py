import tkinter as tk
from tkinter import simpledialog
from PIL import ImageTk, Image
import json
from pathlib import Path

IMAGE_PATH = "images/with_mark.png"
JSON_PATH = "data/holds.json"

def load_holds():
    if Path(JSON_PATH).exists():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_holds(holds):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(holds, f, indent=4, ensure_ascii=False)

def on_click(event, holds, canvas, img_width, img_height):
    x, y = event.x, event.y
    # 弹窗让你输入岩点ID
    hold_id = simpledialog.askstring("输入岩点ID", f"点选位置: ({x}, {y})\n请输入岩点ID（如 34 或 a）:")
    if hold_id:
        holds[hold_id] = {"x": x, "y": y}
        save_holds(holds)
        # 标记点
        canvas.create_oval(x-4, y-4, x+4, y+4, outline="green", width=2)
        canvas.create_text(x, y-10, text=hold_id, fill="green", font=("Arial", 12, "bold"))

def main():
    holds = load_holds()
    root = tk.Tk()
    root.title("人工补充岩点工具")

    img = Image.open(IMAGE_PATH)
    img_width, img_height = img.size
    tk_img = ImageTk.PhotoImage(img)

    canvas = tk.Canvas(root, width=img_width, height=img_height)
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=tk_img)

    # 已有点也显示出来
    for hold_id, coord in holds.items():
        x, y = coord["x"], coord["y"]
        canvas.create_oval(x-4, y-4, x+4, y+4, outline="blue", width=2)
        canvas.create_text(x, y-10, text=hold_id, fill="blue", font=("Arial", 12, "bold"))

    canvas.bind("<Button-1>", lambda e: on_click(e, holds, canvas, img_width, img_height))
    root.mainloop()

if __name__ == "__main__":
    main()
