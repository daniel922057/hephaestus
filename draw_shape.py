import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

# 设置绘图
fig, ax = plt.subplots(figsize=(10, 6))

# 定义关键坐标点
# 总宽 127.2
# 延伸部分要求 100 (从 0 到 100 是深的一侧)
# 右侧浅的部分剩余 27.2 (从 100 到 127.2)
# 为了过渡自然，我们需要占用一点过渡空间。
# 设定：
# 0-90cm: 完全平直的深桌面 (y=-25)
# 90-115cm: S型过渡区 (从 y=-25 过渡到 y=0)
# 115-127.2cm: 右侧浅桌面 (y=0)

verts = [
    (0, 30),          # 左上 (起点略下，为了画左上角圆角或直角，这里默认左上直角) -> 其实通常左侧靠墙是直角
    (0, 40),          # 左上角
    (127.2, 40),      # 右上角
    (127.2, 0),       # 右下角 (浅侧)
    (115, 0),         # 过渡起点 (上)
    
    # S型曲线: 从 (115, 0) 优雅地弯到 (95, -25)
    # 控制点1 (110, 0) -> 保持水平出的趋势
    # 控制点2 (100, -25) -> 提前进入垂直趋势
    # 终点 (95, -25)
    (105, 0), (105, -25), (95, -25), 
    
    # 延伸部分底部平直线
    (10, -25),        # 直线走到左下角圆角处
    
    # 左下角大圆角
    (0, -25), (0, -15), # 贝塞尔曲线控制点和终点
    
    # 回到起点
    (0, 30)
]

codes = [
    Path.MOVETO,
    Path.LINETO,
    Path.LINETO,
    Path.LINETO,
    Path.LINETO,
    Path.CURVE4, Path.CURVE4, Path.CURVE4, # S型曲线
    Path.LINETO,
    Path.CURVE3, Path.LINETO, # 左下角圆角
    Path.LINETO
]

path = Path(verts, codes)
patch = patches.PathPatch(path, facecolor='none', lw=2.5, edgecolor='black')
ax.add_patch(patch)

# 设置显示范围和比例
ax.set_xlim(-10, 140)
ax.set_ylim(-40, 60)
ax.set_aspect('equal')

# 隐藏坐标轴刻度，让图纸更干净
ax.axis('off')

# 添加标注
plt.text(63.6, 45, "总宽 127.2 cm", ha='center', fontsize=12)
plt.text(45, -10, "延伸部分 (深 65cm)", ha='center', fontsize=10)
plt.text(45, -30, "有效长度约 100 cm", ha='center', fontsize=10, color='red', weight='bold')

# 标注尺寸线
ax.plot([0, 95], [-28, -28], color='red', lw=1) 
ax.plot([0, 0], [-27, -29], color='red', lw=1)
ax.plot([95, 95], [-27, -29], color='red', lw=1)

# 标题
plt.title("定制设计: 100cm 延伸 + 艺术流线过渡", fontsize=14, pad=20)

plt.tight_layout()
plt.show()