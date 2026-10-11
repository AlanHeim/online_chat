import tkinter as tk
from tkinter import messagebox, scrolledtext
from threading import Thread
from client import ChatClient



class ChatGUI:
    def __init__(self):
        self.client = ChatClient(
            on_message_cb=self.handle_chat_message,
            on_error_cb=self.handle_runtime_error
        )

        self.root = tk.Tk()  # главное окно чата
        self.root.title("чатик")
        self.root.geometry("700x500")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close_application)  # вызвать метод при закрытии окна

        self.root.withdraw()  # спрятать окно

        self.login_window = tk.Toplevel(self.root)  # окно авторизации
        self.login_window.title("Вход в чат")
        self.login_window.geometry("300x150")

        self.login_window.protocol("WM_DELETE_WINDOW", self.on_close_application)

        self.__build_login_widgets()
        self.__build_chat_widgets()

        Thread(target=self.perform_initial_connect, daemon=True).start()  # подключение к серверу
    def __build_login_widgets(self):
        self.login_label = tk.Label(self.login_window,
                                    text="ожидание подключения к серверу...",
                                    font=("Arial", 10))
        self.login_label.pack(pady=(15, 5))

        self.username_entry = tk.Entry(self.login_window,
                                       font=("Arial", 11),
                                       width=25,
                                       state=tk.DISABLED)
        self.username_entry.pack(pady=5)

        self.btn_connect = tk.Button(self.login_window,
                                     text="Войти",
                                     command=self.handle_login_submit,
                                     font=("Arial", 10),
                                     width=10,
                                     state=tk.DISABLED)
        self.btn_connect.pack(pady=10)

        # Привязываем клавишу Enter к окну входа, чтобы можно было входить без клика мышкой
        self.login_window.bind('<Return>', lambda event: self.handle_login_submit())

    def __build_chat_widgets(self):
        """Создает элементы интерфейса внутри главного окна чата."""

        # 1. Большое текстовое поле со встроенным скроллбаром для сообщений
        # wrap=tk.WORD автоматически переносит длинные слова на новую строку
        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Arial", 10))
        # fill=tk.BOTH и expand=True заставляют поле растягиваться при изменении размеров окна
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Делаем поле DISABLED, чтобы пользователь не мог вручную стирать или дописывать сообщения
        self.chat_area.config(state=tk.DISABLED)

        # 2. Нижний контейнер (Frame) для поля ввода и кнопки
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        # 3. Однострочное поле ввода сообщения
        self.msg_entry = tk.Entry(bottom_frame, font=("Arial", 11))
        # side=tk.LEFT прижимает поле к левому краю, а expand=True отдает ему всё свободное место
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # 4. Кнопка "Отправить"
        btn_send = tk.Button(bottom_frame, text="Отправить", command=self.handle_send_message, width=10)
        btn_send.pack(side=tk.RIGHT)

        # Привязываем Enter к главному окну чата для быстрой отправки
        self.root.bind('<Return>', lambda event: self.handle_send_message())

    def perform_initial_connect(self):
        """Фоновый метод для установки связи с сервером при старте."""
        # Вызываем метод клиента и передаем ему наш локальный колбэк (опишем ниже)
        success = self.client.initial_connect(on_login_msg_cb=self.handle_login_message)

        if success:
            # Если связь установлена, активируем интерфейс логина.
            # Помним про потокобезопасность: любые изменения GUI делаем через .after()
            def activate_ui():
                self.username_entry.config(state=tk.NORMAL)
                self.btn_connect.config(state=tk.NORMAL)
                self.username_entry.focus()  # Переводим курсор на поле ввода

            self.root.after(0, activate_ui)
        else:
            # Если сервер выключен или недоступен
            self.root.after(0, lambda: self.login_label.config(text="Сервер недоступен.", fg="red"))

    def handle_login_submit(self):

        """Вызывается при клике на 'Войти' или по нажатию Enter."""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Внимание", "Никнейм не может быть пустым!", parent=self.login_window)
            return

        self.btn_connect.config(state=tk.DISABLED)  #  пока сервер думает

        def auth_worker():
            # Отправляем имя на проверку и передаем тот же локальный колбэк
            success = self.client.send_registration_name(username, on_login_msg_cb=self.handle_login_message)

            if success:
                def open_chat_window():
                    self.login_window.destroy()
                    self.client.start_listen_chat()
                    self.root.deiconify()  # Показываем главное окно чата

                self.root.after(0, open_chat_window)
            else:
                # Если имя занято, включаем кнопку обратно, чтобы пользователь ввел другое имя
                self.root.after(0, lambda: self.btn_connect.config(state=tk.NORMAL))

        Thread(target=auth_worker, daemon=True).start()

    def handle_login_message(self, msg: dict):
        text = msg.get("text")

        def update_label():
            self.login_label.config(text=text)
            if msg.get("status") is False:
                self.login_label.config(fg="red")
            else:
                self.login_label.config(fg="black")
        self.root.after(0, update_label)


    def handle_send_message(self):
        """Берет текст из поля ввода и передает клиенту на отправку."""
        text = self.msg_entry.get().strip()
        if text:
            self.client.send_message(text)
            self.msg_entry.delete(0, tk.END)  # Полностью очищаем поле ввода

    def handle_chat_message(self, msg: dict):
        """Вывод сообщения в чат"""
        user = msg.get("user", "Неизвестный")
        text = msg.get("text", "")

        def safe_insert():
            self.chat_area.config(state=tk.NORMAL) # Временно разрешаем редактирование
            self.chat_area.insert(tk.END, f"[{user}]: {text}\n") # Вставляем текст в самый конец
            self.chat_area.config(state=tk.DISABLED) # Снова блокируем
            self.chat_area.yview(tk.END) # Автоматически скроллим чат вниз к новому сообщению

        self.root.after(0, safe_insert)

    def handle_runtime_error(self, text: str):
        """вывод сообщения об ошибке"""
        self.root.after(0, lambda: messagebox.showerror("Ошибка сети", text))

    def on_close_application(self):
        self.client.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ChatGUI()
    app.run()