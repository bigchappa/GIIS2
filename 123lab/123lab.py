import math
import tkinter as tk
from tkinter import Menu, ttk, messagebox

class DebugWindow(tk.Toplevel):
    def __init__(self, master, width, height, offset_x=0, offset_y=0):
        super().__init__(master)
        self.title("Режим отладки")
        self.cell_size = 8
        self.width = width
        self.height = height
        self.offset_x = offset_x   
        self.offset_y = offset_y  
        
        
        canvas_width = width * self.cell_size
        canvas_height = height * self.cell_size
        self.geometry(f"{canvas_width}x{canvas_height}")
        
        self.canvas = tk.Canvas(self, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.debug_steps = []
        self.current_step = 0
        self.animation_id = None
        self.drawn_points = set()   
        
    def draw_grid(self):
        self.canvas.delete("all")
       
        for x in range(0, self.width * self.cell_size, self.cell_size):
            self.canvas.create_line(x, 0, x, self.height * self.cell_size, fill="#EEE")
        for y in range(0, self.height * self.cell_size, self.cell_size):
            self.canvas.create_line(0, y, self.width * self.cell_size, y, fill="#EEE")
            
    def draw_pixel(self, x, y):
        if (x, y) not in self.drawn_points:
            
            adj_x = x + self.offset_x
            adj_y = y + self.offset_y
            x0 = adj_x * self.cell_size
            y0 = adj_y * self.cell_size
            self.canvas.create_rectangle(
                x0, y0,
                x0 + self.cell_size,
                y0 + self.cell_size,
                fill="black",
                outline=""
            )
            self.drawn_points.add((x, y))
        
    def show_step(self, step):
        
        for i in range(self.current_step + 1):
            if i < len(self.debug_steps):
                x = self.debug_steps[i]['x']
                y = self.debug_steps[i]['y']
                self.draw_pixel(x, y)
        
        
        if step:
            info_text = f"Шаг {self.current_step + 1}\n({step['x']}, {step['y']})"
            if 'error' in step:
                info_text += f"\nОшибка: {step['error']}"
            self.canvas.create_text(
                10, 10,
                anchor=tk.NW,
                text=info_text,
                font=("Arial", 8),
                fill="red"
            )

class GraphicsEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")
        self.root.geometry("1000x1000")
        self.offset_x = 0
        self.offset_y = 0
        self.zoom_level = 1.0
        self.cell_size = 8
        self.current_mode = "line"
        self.curve_params = {}
        self.canvas_offset_x = 400 
        self.canvas_offset_y = 400

        self.create_menu()

        
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        
        input_frame = ttk.Frame(control_frame)
        input_frame.grid(row=0, column=0, padx=5)

        
        ttk.Label(input_frame, text="X0:").grid(row=0, column=0, padx=2)
        self.x0_entry = ttk.Entry(input_frame, width=5)
        self.x0_entry.grid(row=0, column=1, padx=2)
        
        ttk.Label(input_frame, text="Y0:").grid(row=0, column=2, padx=2)
        self.y0_entry = ttk.Entry(input_frame, width=5)
        self.y0_entry.grid(row=0, column=3, padx=2)
        
        ttk.Label(input_frame, text="X1:").grid(row=0, column=4, padx=2)
        self.x1_entry = ttk.Entry(input_frame, width=5)
        self.x1_entry.grid(row=0, column=5, padx=2)
        
        ttk.Label(input_frame, text="Y1:").grid(row=0, column=6, padx=2)
        self.y1_entry = ttk.Entry(input_frame, width=5)
        self.y1_entry.grid(row=0, column=7, padx=2)

        
        self.algorithm_var = tk.StringVar(value="dda")
        algo_frame = ttk.Frame(input_frame)
        algo_frame.grid(row=0, column=8, padx=5)
        
        ttk.Radiobutton(algo_frame, text="ЦДА", variable=self.algorithm_var, 
                       value="dda").pack(side=tk.LEFT)
        ttk.Radiobutton(algo_frame, text="Брезенхем", variable=self.algorithm_var,
                       value="bresenham").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(algo_frame, text="Ву", variable=self.algorithm_var,
                       value="wu").pack(side=tk.LEFT)

        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=9, padx=5)
        
        ttk.Button(btn_frame, text="Построить линию", 
                  command=self.draw_line).pack(side=tk.LEFT)
        
        self.debug_var = tk.BooleanVar()
        ttk.Checkbutton(btn_frame, text="Отладка", 
                       variable=self.debug_var).pack(side=tk.LEFT, padx=5)

        
        curve_frame = ttk.Frame(control_frame)
        curve_frame.grid(row=0, column=1, padx=10, sticky=tk.W)
        
        ttk.Label(curve_frame, text="Кривые:").pack(side=tk.LEFT)
        self.curve_type = tk.StringVar(value="circle")
        ttk.Combobox(curve_frame, textvariable=self.curve_type, 
                    values=["окружность", "эллипс", "гипербола", "парабола"],
                    state="readonly", width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(curve_frame, text="Построить", 
                  command=self.draw_curve).pack(side=tk.LEFT)

        
        
        self.curve_points = []
        self.current_curve_type = "hermite"

        
        self.canvas = tk.Canvas(
            self.main_frame,
            width=800,
            height=800,
            bg="white"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.zoom_level = 1.0     
        self.offset_x = 0         
        self.offset_y = 0         
        self.drag_start = None

        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)

        
        self.debug_window = None

        self.setup_curve_ui()

    def create_menu(self):
        menubar = Menu(self.root)
        
        curves_menu = Menu(menubar, tearoff=0)
        curves_menu.add_command(label="Окружность", command=lambda: self.set_curve_mode("circle"))
        curves_menu.add_command(label="Эллипс", command=lambda: self.set_curve_mode("ellipse"))
        curves_menu.add_command(label="Гипербола", command=lambda: self.set_curve_mode("hyperbola"))
        curves_menu.add_command(label="Парабола", command=lambda: self.set_curve_mode("parabola"))
        
        menubar.add_cascade(label="Линии второго порядка", menu=curves_menu)
        self.root.config(menu=menubar)

    def get_coordinates(self):
        try:
            max_coord = 800 // self.cell_size  
            
            x0 = int(self.x0_entry.get())
            y0 = int(self.y0_entry.get())
            x1 = int(self.x1_entry.get())
            y1 = int(self.y1_entry.get())
            
           
            if any(abs(val) > max_coord for val in [x0, y0, x1, y1]):
                messagebox.showerror("Ошибка", 
                    f"Координаты должны быть в пределах ±{max_coord}")
                return None, None
                
            return (x0, y0), (x1, y1)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целые числа для координат")
            return None, None

    def draw_line(self):
        start, end = self.get_coordinates()
        if not start or not end:
            return
        
        algorithm = self.algorithm_var.get()
        if algorithm == "dda":
            points, self.debug_steps = self.dda(start, end)
        elif algorithm == "bresenham":
            points, self.debug_steps = self.bresenham(start, end)
        elif algorithm == "wu":
            points, self.debug_steps = self.wu(start, end)
        
        self.canvas.delete("all")
        self.draw_points(points)
        
        if self.debug_var.get():
            
            center_x = (start[0] + end[0]) // 2
            center_y = (start[1] + end[1]) // 2
            self.show_debug_window(self.debug_steps, center_x, center_y)

    def setup_curve_ui(self):
        
        curve_control_frame = ttk.Frame(self.main_frame)
        curve_control_frame.pack(fill=tk.X, pady=5, before=self.canvas)

        
        self.curve_type_var = tk.StringVar(value="hermite")
        curve_type_combo = ttk.Combobox(
            curve_control_frame,
            textvariable=self.curve_type_var,
            values=["hermite", "bezier", "bspline"],
            state="readonly",
            width=10
        )
        curve_type_combo.pack(side=tk.LEFT, padx=5)

        
        ttk.Button(curve_control_frame, text="Добавить точку", 
                  command=self.add_curve_point).pack(side=tk.LEFT, padx=5)
        ttk.Button(curve_control_frame, text="Очистить точки", 
                  command=self.clear_curve_points).pack(side=tk.LEFT, padx=5)
        ttk.Button(curve_control_frame, text="Построить кривую", 
                  command=self.draw_current_curve).pack(side=tk.LEFT, padx=5)
        

    def show_debug_window(self, debug_steps, center_x=0, center_y=0):
        
        window_size = 100  
        offset_x = (window_size // 2) - center_x
        offset_y = (window_size // 2) - center_y
        
        if not self.debug_window or not self.debug_window.winfo_exists():
            self.debug_window = DebugWindow(
                self.root, 
                width=window_size,
                height=window_size,
                offset_x=offset_x,
                offset_y=offset_y
            )
        
        self.debug_window.debug_steps = debug_steps
        self.debug_window.current_step = 0
        self.debug_window.drawn_points.clear()
        self.debug_window.draw_grid()
        self.animate_step()


    def animate_step(self):
        if self.debug_window and self.debug_window.winfo_exists():
            if self.debug_window.current_step < len(self.debug_window.debug_steps):
                step = self.debug_window.debug_steps[self.debug_window.current_step]
                self.debug_window.show_step(step)
                self.debug_window.current_step += 1
                self.debug_window.animation_id = self.root.after(50, self.animate_step)

    def close_debug(self):
        if self.debug_window:
            if self.debug_window.animation_id:
                self.root.after_cancel(self.debug_window.animation_id)
            self.debug_window.destroy()
        self.debug_var.set(False)

    def transform_coords(self, x, y):
        
        return (
            int(800/2 + (x * self.cell_size - self.offset_x) * self.zoom_level),
            int(800/2 + (y * self.cell_size - self.offset_y) * self.zoom_level)
        )

    def zoom(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_level *= scale_factor
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))  
        self.redraw_all()

    def redraw_all(self):
        
        self.canvas.delete("all")
        if hasattr(self, 'last_drawn_points'):
            self.draw_points(self.last_drawn_points)

    def start_drag(self, event):
        self.drag_start = (event.x, event.y)

    def drag(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.offset_x += dx / self.zoom_level
            self.offset_y += dy / self.zoom_level
            self.drag_start = (event.x, event.y)
            self.redraw_all()

    def draw_points(self, points):
        for point in points:
            if len(point) == 3:
                x, y, color = point
            else:
                x, y = point
                color = "black"
                
            
            screen_x, screen_y = self.transform_coords(x, y)
            
            
            size = max(1, int(self.cell_size * self.zoom_level))
            
            self.canvas.create_rectangle(
                screen_x,
                screen_y,
                screen_x + size,
                screen_y + size,
                fill=color,
                outline=color
            )
        
        
        self.last_drawn_points = points

    def dda(self, start, end):
        debug_steps = []
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return [], []
        
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = x1, y1
        
        points = []
        debug_steps = []
        
        for _ in range(steps + 1):
            rx, ry = round(x), round(y)
            points.append((rx, ry))
            debug_steps.append({'x': rx, 'y': ry})
            x += x_inc
            y += y_inc
        
        for _ in range(steps + 1):
            debug_steps.append({'x': rx, 'y': ry})  
        return points, debug_steps
    def bresenham(self, start, end):
        x1, y1 = start
        x2, y2 = end
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steep = dy > dx
        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx
        
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        
        dx = x2 - x1
        dy = abs(y2 - y1)
        error = dx // 2
        y_step = 1 if y1 < y2 else -1
        y = y1
        
        points = []
        debug_steps = []
        
        for x in range(x1, x2 + 1):
            coord = (y, x) if steep else (x, y)
            points.append(coord)
            debug_steps.append({'x': coord[0], 'y': coord[1], 'error': error})
            error -= dy
            if error < 0:
                y += y_step
                error += dx
        
        return points, debug_steps

    def wu(self, start, end):
        import math
        x1, y1 = start
        x2, y2 = end
        points = []
        debug_steps = []

        def plot(x, y, intensity):
            
            gray = int(255 * intensity)
            color = f'#{gray:02x}{gray:02x}{gray:02x}'
            points.append((x, y, color))
            debug_steps.append({'x': x, 'y': y})

        dx = x2 - x1
        dy = y2 - y1

        steep = abs(dy) > abs(dx)

        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
            dx, dy = dy, dx

        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1

        gradient = dy / dx if dx != 0 else 1.0

        
        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = 1 - (x1 + 0.5) % 1 

        xpxl1 = xend
        yfrac, ywhole = math.modf(yend)
        ypxl1 = int(ywhole)

        if steep:
            
            plot(ypxl1, xpxl1, (1 - yfrac) * xgap)
            plot(ypxl1 + 1, xpxl1, yfrac * xgap)
        else:
            plot(xpxl1, ypxl1, (1 - yfrac) * xgap)
            plot(xpxl1, ypxl1 + 1, yfrac * xgap)

        intery = yend + gradient

        
        xend = round(x2)
        yend = y2 + gradient * (xend - x2)
        xgap = (x2 + 0.5) % 1

        xpxl2 = xend
        yfrac, ywhole = math.modf(yend)
        ypxl2 = int(ywhole)

        if steep:
            plot(ypxl2, xpxl2, (1 - yfrac) * xgap)
            plot(ypxl2 + 1, xpxl2, yfrac * xgap)
        else:
            plot(xpxl2, ypxl2, (1 - yfrac) * xgap)
            plot(xpxl2, ypxl2 + 1, yfrac * xgap)

        
        for x in range(xpxl1 + 1, xpxl2):
            yfrac, ywhole = math.modf(intery)
            y = int(ywhole)
            if steep:
                
                plot(y, x, 1 - yfrac)
                plot(y + 1, x, yfrac)
            else:
                plot(x, y, 1 - yfrac)
                plot(x, y + 1, yfrac)
            intery += gradient

        return points, debug_steps
    

    def set_curve_mode(self, mode):
        self.current_mode = mode
        self.show_curve_parameters()

    def show_curve_parameters(self):
       
        param_window = tk.Toplevel(self.root)
        param_window.title("Параметры кривой")
        
        params = []
        if self.current_mode == "circle":
            params = [("Радиус:", "radius")]
        elif self.current_mode == "ellipse":
            params = [("Большая ось (a):", "a"), ("Малая ось (b):", "b")]
        elif self.current_mode == "hyperbola":
            params = [("Параметр a:", "a"), ("Параметр b:", "b")]
        elif self.current_mode == "parabola":
            params = [("Параметр p:", "p")]
        
        entries = {}
        for i, (label, key) in enumerate(params):
            ttk.Label(param_window, text=label).grid(row=i, column=0, padx=5, pady=2)
            entry = ttk.Entry(param_window, width=10)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries[key] = entry
        
        def save_params():
            try:
                for key, entry in entries.items():
                    self.curve_params[key] = float(entry.get())
                param_window.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректные значения параметров")
        
        ttk.Button(param_window, text="Применить", command=save_params).grid(
            row=len(params), columnspan=2, pady=5)

    def draw_curve(self):
        if not self.curve_params:
            messagebox.showwarning("Ошибка", "Сначала задайте параметры кривой")
            return
        
        try:
            x0 = int(self.x0_entry.get() or 0)
            y0 = int(self.y0_entry.get() or 0)
        except ValueError:
            messagebox.showerror("Ошибка", "Координаты центра должны быть целыми числами")
            return

        points = []
        debug_steps = [] 

        if self.current_mode == "circle":
            if "radius" not in self.curve_params:
                messagebox.showerror("Ошибка", "Не задан радиус")
                return
            points, debug_steps = self.bresenham_circle(x0, y0, self.curve_params["radius"])
        
        elif self.current_mode == "ellipse":
            if "a" not in self.curve_params or "b" not in self.curve_params:
                messagebox.showerror("Ошибка", "Задайте параметры a и b для эллипса")
                return
            points, debug_steps = self.midpoint_ellipse(
                x0, y0, 
                self.curve_params["a"], 
                self.curve_params["b"]
            )

        elif self.current_mode == "hyperbola":
            if "a" not in self.curve_params or "b" not in self.curve_params:
                messagebox.showerror("Ошибка", "Задайте параметры a и b для гиперболы")
                return
            points, debug_steps = self.bresenham_hyperbola(
                x0, y0,
                self.curve_params["a"],
                self.curve_params["b"]
            )

        elif self.current_mode == "parabola":
            if "p" not in self.curve_params:
                messagebox.showerror("Ошибка", "Задайте параметр p для параболы")
                return
            points, debug_steps = self.midpoint_parabola(
                x0, y0,
                self.curve_params["p"]
            )

        self.canvas.delete("all")
        self.draw_points(points)
        
        if self.debug_var.get():
            
            self.show_debug_window(debug_steps, x0, y0)

    def bresenham_hyperbola(self, xc, yc, a, b):
        points = []
        debug_steps = []
        x = a
        y = 0
        a_sq = a * a
        b_sq = b * b
        d = 2 * a_sq - 2 * a * b_sq - b_sq
        
        while x <= 200:
            self.add_hyperbola_points(xc, yc, x, y, points, debug_steps)
            debug_steps.append({'x': xc + x, 'y': yc + y, 'error': d})
            
            if d < 0:
                d += 2 * a_sq * (2 * y + 3)
            else:
                d += 2 * a_sq * (2 * y + 3) - 4 * b_sq * (x + 1)
                x += 1
            y += 1
        
        return points, debug_steps

    
    def add_hyperbola_points(self, xc, yc, x, y, points, debug_steps):
        max_coord = 800 // self.cell_size
        for sx, sy in [(1,1), (1,-1)]:  
            xi = xc + x * sx
            yi = yc + y * sy
            if abs(xi) <= max_coord and abs(yi) <= max_coord:
                points.append((xi, yi))
                debug_steps.append({'x': xi, 'y': yi})

    def midpoint_parabola(self, xc, yc, p):
        points = []
        debug_steps = []
        x = 0
        y = 0
        d = 1 - p
        
        while x <= 200:
            self.add_parabola_points(xc, yc, x, y, points, debug_steps)
            debug_steps.append({'x': xc + x, 'y': yc + y, 'error': d})
            
            if d < 0:
                d += 2 * y + 3
            else:
                d += 2 * y + 3 - 4 * p
                x += 1
            y += 1
        
        return points, debug_steps

    def add_parabola_points(self, xc, yc, x, y, points, debug_steps):
        max_coord = 800 // self.cell_size
        for sy in [1, -1]:  
            xi = xc + x
            yi = yc + y * sy
            if abs(xi) <= max_coord and abs(yi) <= max_coord:
                points.append((xi, yi))
                debug_steps.append({'x': xi, 'y': yi})

    
    def bresenham_circle(self, xc, yc, r):
        points = []
        debug_steps = []
        x = 0
        y = r
        delta = 2 - 2 * r 
        limit = 0  

        while y > limit:
            
            self.add_circle_points(xc, yc, x, y, points, debug_steps)
            
            delta_star = 2 * delta - 2 * x - 1
            
            if delta_star > 0:
                y -= 1
                delta += -2 * y + 1
            else:
                delta_new = 2 * delta + 2 * y - 1
                if delta_new > 0:
                    x += 1
                    y -= 1
                    delta += 2 * (x - y) + 2
                else:
                    x += 1
                    delta += 2 * x + 1
            
            debug_steps.append({
                'x': xc + x,
                'y': yc + y,
                'error': delta,
                'action': 'V' if delta_star > 0 else 'D' if delta_new > 0 else 'H'
            })
        
        return points, debug_steps

    def add_circle_points(self, xc, yc, x, y, points, debug_steps):
        max_coord = 800 // self.cell_size
        for sx, sy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
            for px, py in [(x, y), (y, x)]:
                xi = xc + px*sx
                yi = yc + py*sy
                if abs(xi) <= max_coord and abs(yi) <= max_coord:
                    points.append((xi, yi))
                    debug_steps.append({'x': xi, 'y': yi})

    
    def midpoint_ellipse(self, xc, yc, a, b):
        points = []
        debug_steps = []
        x = 0
        y = b
        a2 = a * a
        b2 = b * b
        delta = a2 + b2 - 2 * a2 * b 

        while y >= 0:
            self.add_ellipse_points(xc, yc, x, y, points, debug_steps)
            debug_steps.append({'x': xc + x, 'y': yc + y, 'error': delta})

            if delta < 0:
                delta_star = 2 * (delta + a2 * y) - 1
                if delta_star <= 0:
                    delta += b2 * (2 * x + 1)
                    x += 1
                else:
                    delta += b2 * (2 * x + 1) + a2 * (1 - 2 * y)
                    x += 1
                    y -= 1
            elif delta > 0:
                delta_star = 2 * (delta - b2 * x) - 1
                if delta_star <= 0:
                    delta += b2 * (2 * x + 1) + a2 * (1 - 2 * y)
                    x += 1
                    y -= 1
                else:
                    delta += a2 * (1 - 2 * y)
                    y -= 1
            else:
                delta += b2 * (2 * x + 1) + a2 * (1 - 2 * y)
                x += 1
                y -= 1

        return points, debug_steps

    def add_ellipse_points(self, xc, yc, x, y, points, debug_steps):
        for sx, sy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
            points.append((xc + x*sx, yc + y*sy))
            debug_steps.append({'x': xc + x*sx, 'y': yc + y*sy})

    def add_curve_point(self):
        try:
            x = int(self.x0_entry.get())
            y = int(self.y0_entry.get())
            self.curve_points.append((x, y))
            messagebox.showinfo("Точка добавлена", f"Точка ({x}, {y}) добавлена")
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные координаты точки")

    def clear_curve_points(self):
        self.curve_points = []
        self.canvas.delete("all")

    def draw_current_curve(self):
        if len(self.curve_points) < 2:
            messagebox.showerror("Ошибка", "Добавьте минимум 2 точки")
            return

        curve_type = self.curve_type_var.get()
        points = []
        debug_steps = []

        if curve_type == "hermite":
            points, debug_steps = self.draw_hermite()
        elif curve_type == "bezier":
            points, debug_steps = self.draw_bezier()
        elif curve_type == "bspline":
            points, debug_steps = self.draw_bspline()

        self.draw_points(points)
        
        if self.debug_var.get():
            self.show_debug_window(debug_steps)


    def draw_hermite(self):
        points = []
        debug_steps = []
        for i in range(len(self.curve_points) - 1):
            p0 = self.curve_points[i]
            p1 = self.curve_points[i + 1]
            
            t0 = 0
            if i > 0:
                t0 = (p1[0] - self.curve_points[i-1][0]) / 2
                
            t1 = 0
            if i < len(self.curve_points) - 2:
                t1 = (self.curve_points[i+2][0] - p0[0]) / 2

            for t in [x * 0.01 for x in range(101)]:
                h1 = 2*t**3 - 3*t**2 + 1
                h2 = -2*t**3 + 3*t**2
                h3 = t**3 - 2*t**2 + t
                h4 = t**3 - t**2
                
                x = h1*p0[0] + h2*p1[0] + h3*t0 + h4*t1
                y = h1*p0[1] + h2*p1[1] + h3*t0 + h4*t1
                
                points.append((round(x), round(y)))
                debug_steps.append({'x': round(x), 'y': round(y)})
        
        return points, debug_steps

    def draw_bezier(self):
        points = []
        debug_steps = []
        n_segments = (len(self.curve_points) - 1) // 3
        if (len(self.curve_points) - 1) % 3 != 0:
            messagebox.showerror("Ошибка", 
                "Для кривой Безье нужно 3n+1 точек (4,7,10...)")
            return [], []

        for seg in range(n_segments):
            i = seg * 3
            p0 = self.curve_points[i]
            p1 = self.curve_points[i+1]
            p2 = self.curve_points[i+2]
            p3 = self.curve_points[i+3]

            for t in [x * 0.001 for x in range(1001)]:
                x = (1-t)**3 * p0[0] + 3*(1-t)**2*t*p1[0] + \
                    3*(1-t)*t**2*p2[0] + t**3*p3[0]
                y = (1-t)**3 * p0[1] + 3*(1-t)**2*t*p1[1] + \
                    3*(1-t)*t**2*p2[1] + t**3*p3[1]
                
                points.append((round(x), round(y)))
                debug_steps.append({'x': round(x), 'y': round(y)})
        
        return points, debug_steps

    def draw_bspline(self):
        import numpy as np
        points = []
        debug_steps = []
        
        if len(self.curve_points) < 4:
            messagebox.showerror("Ошибка", 
                "Для B-сплайна нужно минимум 4 точки")
            return [], []

        
        n = len(self.curve_points)
        degree = 3
        knots = np.arange(n + degree + 1)
        
        t = np.linspace(degree, n - 1, 1000)
        basis = np.zeros((len(t), n))
        
        for i in range(n):
            basis[:,i] = self.bspline_basis(i, degree, knots, t)
        
        curve = np.dot(basis, self.curve_points)
        
        for x, y in curve:
            points.append((int(x), int(y)))
            debug_steps.append({'x': int(x), 'y': int(y)})
        
        return points, debug_steps

    def bspline_basis(self, i, k, knots, t):
        if k == 0:
            return ((knots[i] <= t) & (t < knots[i+1])).astype(float)
        else:
            denom1 = knots[i+k] - knots[i]
            term1 = 0 if denom1 == 0 else (t - knots[i])/denom1 * \
                    self.bspline_basis(i, k-1, knots, t)
            
            denom2 = knots[i+k+1] - knots[i+1]
            term2 = 0 if denom2 == 0 else (knots[i+k+1] - t)/denom2 * \
                    self.bspline_basis(i+1, k-1, knots, t)
            
            return term1 + term2

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphicsEditor(root)
    root.mainloop()