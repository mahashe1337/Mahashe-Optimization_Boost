import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import ctypes
import subprocess
import requests
import zipfile
import io
import winreg

RAMMAP_URL = "https://download.sysinternals.com/files/RAMMap.zip"
RAMMAP_EXE = "RAMMap.exe"

# Проверка прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Скачивание RAMMap
def download_rammap():
    try:
        rammap_path = os.path.join(os.getcwd(), RAMMAP_EXE)
        if not os.path.exists(rammap_path):
            messagebox.showinfo("Загрузка", "Скачиваем RAMMap...")
            r = requests.get(RAMMAP_URL)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                z.extractall(os.getcwd())
            # Удаляем лишние файлы после распаковки
            eula_path = os.path.join(os.getcwd(), "eula.txt")
            rammap64a_path = os.path.join(os.getcwd(), "RAMMap64a.exe")
            for f in [eula_path, rammap64a_path]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"Не удалось удалить {f}: {e}")
            messagebox.showinfo("Готово", "RAMMap скачан и распакован.")
        return rammap_path
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить RAMMap: {e}")
        return None


# 1. Оптимизация
def optimize_for_games():
    rammap_path = download_rammap()
    if rammap_path and os.path.exists(rammap_path):
        try:
            subprocess.run([rammap_path, "-Et"], shell=True)  # Очистка памяти
            messagebox.showinfo("Готово", "Память очищена через RAMMap.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить память: {e}")

# 2. Настройки реестра для игр
GAMES_REG_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
GAMES_SETTINGS = {
    "GPU Priority": 8,
    "Priority": 6,
    "Scheduling Category": "High",
    "SFIO Priority": "High"
}

def apply_game_profile():
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, GAMES_REG_PATH)
        for name, value in GAMES_SETTINGS.items():
            if isinstance(value, int):
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            else:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        messagebox.showinfo("Готово", "Игровой профиль применён.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось применить настройки: {e}")
    update_game_profile_status()

def check_game_profile_status():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, GAMES_REG_PATH)
        all_set = True
        partial = False
        for name, value in GAMES_SETTINGS.items():
            try:
                val, regtype = winreg.QueryValueEx(key, name)
                if val != value:
                    all_set = False
                    partial = True
            except FileNotFoundError:
                all_set = False
        winreg.CloseKey(key)
        if all_set:
            return "✅"
        elif partial:
            return "⚠️"
        else:
            return "❌"
    except FileNotFoundError:
        return "❌"

def update_game_profile_status():
    status = check_game_profile_status()
    lbl_game_profile_status.config(text=status)

# 3. Добавление процесса в Image File Execution Options с высоким приоритетом
def add_process_high_priority():
    filepath = filedialog.askopenfilename(title="Выберите исполняемый файл (.exe)", filetypes=[("EXE files", "*.exe")])
    if not filepath:
        return
    proc_name = os.path.basename(filepath)
    try:
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{}\PerfOptions".format(proc_name)
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        # 0x00000003 = High Priority
        winreg.SetValueEx(key, "CpuPriorityClass", 0, winreg.REG_DWORD, 3)
        winreg.CloseKey(key)
        messagebox.showinfo("Готово", f"Процесс {proc_name} теперь будет запускаться с высоким приоритетом.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось добавить процесс: {e}")

# Удаление процесса из Image File Execution Options
def remove_process_high_priority_by_name(proc_name):
    try:
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{}".format(proc_name)
        # Удаляем подветку PerfOptions, если есть
        try:
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, reg_path + r"\PerfOptions")
        except FileNotFoundError:
            pass
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        messagebox.showinfo("Готово", f"Процесс {proc_name} удалён из настроек высокого приоритета.")
    except FileNotFoundError:
        messagebox.showinfo("Информация", f"Процесс {proc_name} не найден в реестре.")
    except OSError as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить процесс: {e}")

def remove_process_high_priority():
    filepath = filedialog.askopenfilename(title="Выберите исполняемый файл (.exe) для удаления из реестра",
                                          filetypes=[("EXE files", "*.exe")])
    if not filepath:
        return
    proc_name = os.path.basename(filepath)
    remove_process_high_priority_by_name(proc_name)

# Показать список процессов с высоким приоритетом
def show_high_priority_processes():
    window = tk.Toplevel(root)
    window.title("Процессы с высоким приоритетом")
    window.geometry("400x300")
    window.configure(bg="#222222")

    lbl = tk.Label(window, text="Выберите процесс для удаления", bg="#222222", fg="white", font=("Arial", 12))
    lbl.pack(pady=5)

    listbox = tk.Listbox(window, bg="#333333", fg="white", font=("Arial", 12), selectmode=tk.SINGLE)
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Собираем процессы из реестра
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options")
        i = 0
        procs = []
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                i += 1
                # Проверим, есть ли у этого процесса ключ PerfOptions с CpuPriorityClass=3
                try:
                    perf_key_path = r"{}\PerfOptions".format(subkey_name)
                    perf_key = winreg.OpenKey(key, perf_key_path)
                    val, regtype = winreg.QueryValueEx(perf_key, "CpuPriorityClass")
                    winreg.CloseKey(perf_key)
                    if val == 3:
                        procs.append(subkey_name)
                except FileNotFoundError:
                    pass
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось получить список процессов: {e}")
        window.destroy()
        return

    for proc in procs:
        listbox.insert(tk.END, proc)

    def delete_selected():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите процесс для удаления.")
            return
        proc_name = listbox.get(sel[0])
        if messagebox.askyesno("Подтверждение", f"Удалить процесс {proc_name} из высокого приоритета?"):
            remove_process_high_priority_by_name(proc_name)
            listbox.delete(sel[0])

    btn_delete = tk.Button(window, text="Удалить выбранный процесс", command=delete_selected,
                           font=("Arial", 12), bg="#ff4444", fg="white")
    btn_delete.pack(pady=10)

# GUI
root = tk.Tk()
root.title("Mahashe Game Booster")
root.geometry("520x450")
root.configure(bg="#222222")

logo = tk.Label(root, text="🅼 Mahashe", font=("Arial", 24, "bold"), fg="white", bg="#222222")
logo.pack(pady=20)


frame_game_profile = tk.Frame(root, bg="#222222")
frame_game_profile.pack(pady=5)
btn_game_profile = tk.Button(frame_game_profile, text="🎮 Применить игровой профиль", command=apply_game_profile,
                             font=("Arial", 12), bg="#3399ff", fg="white", width=30)
btn_game_profile.pack(side=tk.LEFT)

lbl_game_profile_status = tk.Label(frame_game_profile, text="", font=("Arial", 20), fg="white", bg="#222222", width=3)
lbl_game_profile_status.pack(side=tk.LEFT, padx=10)

btn_add_process = tk.Button(root, text="📌 Добавить процесс с высоким приоритетом", command=add_process_high_priority,
                            font=("Arial", 12), bg="#4a0505", fg="white", width=40)
btn_add_process.pack(pady=10)

btn_remove_process = tk.Button(root, text="❌ Удалить процесс из высокого приоритета", command=remove_process_high_priority,
                               font=("Arial", 12), bg="#4a0505", fg="white", width=40)
btn_remove_process.pack(pady=5)

btn_optimize = tk.Button(root, text="🚀 Оптимизация (RAMMap)", command=optimize_for_games,
                         font=("Arial", 12), bg="#6f47ff", fg="white", width=40)
btn_optimize.pack(pady=10)
btn_show_list = tk.Button(root, text="📋 Показать процессы с высоким приоритетом", command=show_high_priority_processes,
                          font=("Arial", 12), bg="#3399ff", fg="white", width=40)
btn_show_list.pack(pady=10)

if not is_admin():
    messagebox.showwarning("Требуются права администратора", "Перезапустите программу с правами администратора.")

update_game_profile_status()

root.mainloop()
