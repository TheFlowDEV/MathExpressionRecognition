import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import os
from gradio_client import Client, handle_file
import datetime
import sys
import io
import threading
class FormulaApp:
    def __init__(self, main_window):
#Инициализация главного окна приложения и всех компоненнтов
        self.root = main_window
        self.root.title("Распознавание формул")

        # Клиент для API распознавания формул (используется PosFormer модель)
        self.api_client = Client("FlowKal/PosFormer_TPU_Practice")
        # Размеры холста для рисования
        self.canvas_width = 500
        self.canvas_height = 300
        self.pen_color = "black" # Цвет по умолчанию для рисования

        # Создание холста для рисования
        self.canvas = tk.Canvas(main_window, width=self.canvas_width, height=self.canvas_height, bg='white')
        self.canvas.pack(pady=10)

        # Создание изображения в памяти для хранения нарисованного
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)

        # Привязка событий мыши к холсту
        self.canvas.bind("<Button-1>", self.start_draw) # Нажатие кнопки мыши
        self.canvas.bind("<B1-Motion>", self.draw_on_canvas) # Перемещение с нажатой кнопкой

        # Создание панели с кнопками
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        # Кнопки управления
        tk.Button(btn_frame, text="Распознать", command=self.recognize).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Очистить", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сохранить", command=self.save_all).pack(side=tk.LEFT, padx=5)

        # Кнопка ластика с переключением режима
        self.eraser_button = tk.Button(btn_frame, text="Ластик", command=self.toggle_eraser)
        self.eraser_button.pack(side=tk.LEFT, padx=5)

        # Метка для отображения результата распознавания
        self.result_label = tk.Label(root, text="Результат: ", font=("Arial", 12))
        self.result_label.pack(pady=10)

        # Переменные для хранения последней позиции рисования
        self.last_x = None
        self.last_y = None
        self.is_erasing = False # Флаг режима ластика

        # Создание папок для сохранения результатов
        self.draw_folder = "рисунки"
        self.text_folder = "формулы"
        os.makedirs(self.draw_folder, exist_ok=True)
        os.makedirs(self.text_folder, exist_ok=True)

    def start_draw(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def draw_on_canvas(self, event):
        x, y = event.x, event.y

        # Выбор цвета и толщины в зависимости от режима (ластик или карандаш)
        color = "white" if self.is_erasing else self.pen_color
        width = 8 if self.is_erasing else 4

        # Рисование на холсте Tkinter
        self.canvas.create_line(self.last_x, self.last_y, x, y, width=width,
                                fill=color, capstyle=tk.ROUND, smooth=True)
        # Рисование в изображении PIL
        self.draw.line([self.last_x, self.last_y, x, y], fill=color, width=width)

        # Обновление последней позиции
        self.last_x = x
        self.last_y = y

    def toggle_eraser(self):
        #Переключение между режима ластика и карандаша
        self.is_erasing = not self.is_erasing
        self.eraser_button.config(text="Карандаш" if self.is_erasing else "Ластик")

    def clear_canvas(self):
        #Очистка холста и сброс всех параметров
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.result_label.config(text="Результат: ")
        self.is_erasing = False
        self.eraser_button.config(text="Ластик")
    def recognize(self):
    #Запуск распознавания в отдельном потоке
        thread = threading.Thread(target=self._recognize)
        thread.start()
    def _recognize(self):
        # Основная функция распознавания формулы
        # Создание временного файла для изображения
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = f"temp-{timestamp}.bmp"
        self.image.save(path)

        #Отправка изображения в API для распознавания
        result = self.api_client.predict(
            sketchpad_data={"background":None,"layers":[],"composite":handle_file(path)},
            api_name="/predict"
        )
        #Удаление временного файла и обновление результата
        os.remove(path)
        self.result_label.config(text=f"Результат:{result}")

    def get_next_filename(self, folder, prefix, ext):
        i = 1
        while True:
            filename = f"{prefix}_{i}.{ext}"
            full_path = os.path.join(folder, filename)
            if not os.path.exists(full_path):
                return full_path
            i += 1

    def save_all(self):
        # Сохранить рисунок
        image_path = self.get_next_filename(self.draw_folder, "рисунок", "png")
        self.image.save(image_path)

        # Сохранить распознанную формулу
        text = self.result_label.cget("text").replace("Результат: ", "")
        formula_path = self.get_next_filename(self.text_folder, "формула", "txt")
        with open(formula_path, "w", encoding="utf-8") as f:
            f.write(text)
        #Показ сообщения о сохранении
        messagebox.showinfo("Сохранение", f"Изображение и формула сохранены:\n{image_path}\n{formula_path}")

if __name__ == "__main__":
    #Настройка кодировки вывода
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

    #Создание и запуск главного окна
    root = tk.Tk()
    app = FormulaApp(root)
    root.mainloop()
