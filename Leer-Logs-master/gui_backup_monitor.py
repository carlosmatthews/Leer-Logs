import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
import subprocess
import threading
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_backup_list():
    from copy_logs_files import nombre_ultimo_backup
    return list(dict.fromkeys(nombre_ultimo_backup))

class BackupMonitorGUI:
    COLOR_OK = "#90EE90"
    COLOR_ERROR = "#FFD700"
    COLOR_SIN_BACKUP = "#FF6B6B"
    COLOR_ERROR_TEXT = "#8B0000"
    
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Backups")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        self.logs_folder = os.path.join(os.path.expanduser('~'), 'Desktop', "Leer-Logs-master", 'Logs')
        
        self.backup_frames = {}
        self.backup_data = {}
        
        self.setup_ui()
        self.load_results()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        title_label = ttk.Label(main_frame, text="Monitor de Estado de Backups", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=5)

        self.run_btn = ttk.Button(button_frame, text="Ejecutar Monitoreo", 
                                   command=self.run_monitoring)
        self.run_btn.grid(row=0, column=0, padx=5)

        self.refresh_btn = ttk.Button(button_frame, text="Actualizar", 
                                      command=self.load_results)
        self.refresh_btn.grid(row=0, column=1, padx=5)

        ttk.Button(button_frame, text="Seleccionar Carpeta", 
                  command=self.select_folder).grid(row=0, column=2, padx=5)

        self.folder_label = ttk.Label(main_frame, 
                                      text=f"Carpeta: {self.logs_folder}",
                                      font=("Arial", 9))
        self.folder_label.grid(row=2, column=0, columnspan=3, pady=5)

        self.last_update_label = ttk.Label(main_frame, 
                                            text=f"Última actualización: --",
                                            font=("Arial", 10))
        self.last_update_label.grid(row=3, column=0, columnspan=3, pady=5)

        backups_frame = ttk.LabelFrame(main_frame, text="Backups", padding="10")
        backups_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)

        canvas_frame = tk.Frame(backups_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        backups_frame.columnconfigure(0, weight=1)
        backups_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, height=400)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.backups_container = self.scrollable_frame

        self.status_label = ttk.Label(main_frame, text="Listo", relief=tk.SUNKEN)
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))

    def create_backup_cards(self):
        for widget in self.backups_container.winfo_children():
            widget.destroy()
        
        self.backup_frames.clear()
        self.backup_data.clear()

        for i, backup_prefix in enumerate(get_backup_list()):
            backup_name = backup_prefix.replace('-', ' → ').replace('_', ' ').strip().upper()
            backup_name = backup_name[:-1] if backup_name.endswith(' → ') else backup_name
            
            self.backup_data[backup_prefix] = {
                'errores': [], 
                'tiene_backup': False, 
                'archivo': ''
            }
            
            frame = tk.Frame(self.backups_container, relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
            frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
            self.backups_container.columnconfigure(0, weight=1)

            name_label = tk.Label(frame, text=backup_name, 
                                font=("Arial", 11, "bold"), bg="#f0f0f0")
            name_label.grid(row=0, column=0, sticky=tk.W)

            status_label = tk.Label(frame, text="Sin backup", 
                                    font=("Arial", 10), bg="#f0f0f0")
            status_label.grid(row=1, column=0, sticky=tk.W, pady=5)

            errors_label = tk.Label(frame, text="", 
                                    font=("Arial", 9), foreground=self.COLOR_ERROR_TEXT, bg="#f0f0f0")
            errors_label.grid(row=2, column=0, sticky=tk.W)

            self.backup_frames[backup_prefix] = {
                'frame': frame,
                'status': status_label,
                'errors': errors_label,
                'label': name_label,
                'prefix': backup_prefix
            }

            frame.bind("<Button-1>", lambda e, p=backup_prefix: self.show_all_errors(p))
            status_label.bind("<Button-1>", lambda e, p=backup_prefix: self.show_all_errors(p))
            errors_label.bind("<Button-1>", lambda e, p=backup_prefix: self.show_all_errors(p))
            name_label.bind("<Button-1>", lambda e, p=backup_prefix: self.show_all_errors(p))

    def show_all_errors(self, backup_prefix):
        data = self.backup_data.get(backup_prefix)
        if not data or not data['errores']:
            return
        
        backup_name = backup_prefix.replace('-', ' → ').replace('_', ' ').strip().upper()
        
        error_win = tk.Toplevel(self.root)
        error_win.title(f"Errores - {backup_name}")
        error_win.geometry("800x500")
        
        tk.Label(error_win, text=f"Errores en {backup_name} ({len(data['errores'])} errores)", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(error_win, width=90, height=25)
        text_area.pack(padx=10, pady=10)
        
        for error in data['errores']:
            text_area.insert(tk.END, f"Línea {error['linea']}: {error['mensaje']}\n")
        
        text_area.config(state=tk.DISABLED)
        
        tk.Button(error_win, text="Cerrar", command=error_win.destroy).pack(pady=10)

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.logs_folder)
        if folder:
            self.logs_folder = folder
            self.folder_label.config(text=f"Carpeta: {self.logs_folder}")
            self.load_results()

    def run_monitoring(self):
        self.run_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Ejecutando monitoreo...")
        self.progress.start(10)

        def run_script():
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                script_path = os.path.join(script_dir, 'readlogs02.py')
                if os.path.exists(script_path):
                    subprocess.run(['python', script_path, self.logs_folder], check=True, cwd=script_dir)
                else:
                    messagebox.showwarning("Advertencia", 
                                           "No se encontró readlogs02.py")
                self.root.after(0, self.load_results)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self.finish_monitoring)

        threading.Thread(target=run_script, daemon=True).start()

    def finish_monitoring(self):
        self.progress.stop()
        self.run_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Monitoreo completado")

    def get_latest_log_file(self):
        if not os.path.exists(self.logs_folder):
            return None
        
        log_files = []
        for f in os.listdir(self.logs_folder):
            if f.startswith('Logs_status') and f.endswith('.txt'):
                log_files.append(os.path.join(self.logs_folder, f))
        
        if log_files:
            return max(log_files, key=os.path.getmtime)
        return None

    def load_results(self):
        self.create_backup_cards()

        latest_file = self.get_latest_log_file()
        
        errors_count = 0
        current_backup = None

        if latest_file and os.path.exists(latest_file):
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line_stripped = line.strip()
                        
                        if line_stripped.startswith("Analizando archivo:"):
                            filename = line_stripped.replace("Analizando archivo:", "").strip().replace("...", "")
                            current_backup = None
                            
                            for backup_prefix in get_backup_list():
                                if filename.startswith(backup_prefix):
                                    self.backup_data[backup_prefix]['tiene_backup'] = True
                                    self.backup_data[backup_prefix]['archivo'] = filename
                                    self.backup_data[backup_prefix]['es_parcial'] = False
                                    current_backup = backup_prefix
                                    break

                        elif "Se encontraron" in line_stripped and "errores en" in line_stripped:
                            pass

                        elif "code 23" in line_stripped:
                            if current_backup and current_backup in self.backup_data:
                                self.backup_data[current_backup]['es_parcial'] = True

                        elif line_stripped.startswith("Línea ") and "rsync error:" not in line_stripped:
                            if current_backup and current_backup in self.backup_data:
                                mensaje = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else line_stripped
                                self.backup_data[current_backup]['errores'].append({
                                    'linea': line_stripped.split()[1].replace(":", ""),
                                    'mensaje': mensaje[:150]
                                })
                                errors_count += 1

                        elif "No se encontraron errores" in line_stripped:
                            current_backup = None

                file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
                self.last_update_label.config(
                    text=f"Última actualización: {file_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Error al leer el archivo: {e}")

        self.update_backup_display(errors_count)

    def update_backup_display(self, total_errors):
        for backup_prefix, data in self.backup_data.items():
            frame_info = self.backup_frames[backup_prefix]
            
            if not data['tiene_backup']:
                frame_info['status'].config(text="✗ Sin backup", foreground=self.COLOR_SIN_BACKUP, font=("Arial", 11, "bold"))
                frame_info['errors'].config(text="")
                frame_info['frame'].config(bg=self.COLOR_SIN_BACKUP)
                frame_info['status'].config(background=self.COLOR_SIN_BACKUP)
                frame_info['errors'].config(background=self.COLOR_SIN_BACKUP)
                frame_info['label'].config(background=self.COLOR_SIN_BACKUP)
                
            elif data.get('es_parcial'):
                frame_info['status'].config(text=f"⚠ Parcial ({len(data['errores'])})", 
                                            foreground=self.COLOR_ERROR_TEXT, font=("Arial", 11, "bold"))
                errores_text = "\n".join([f"Línea {e['linea']}: {e['mensaje'][:80]}..." for e in data['errores'][:3]])
                if len(data['errores']) > 3:
                    errores_text += f"\n... y {len(data['errores']) - 3} más"
                frame_info['errors'].config(text=errores_text)
                frame_info['frame'].config(bg=self.COLOR_ERROR)
                frame_info['status'].config(background=self.COLOR_ERROR)
                frame_info['errors'].config(background=self.COLOR_ERROR)
                frame_info['label'].config(background=self.COLOR_ERROR)
                
            elif data['errores']:
                frame_info['status'].config(text=f"✗ Error ({len(data['errores'])})", 
                                            foreground="red", font=("Arial", 11, "bold"))
                errores_text = "\n".join([f"Línea {e['linea']}: {e['mensaje'][:80]}..." for e in data['errores'][:3]])
                if len(data['errores']) > 3:
                    errores_text += f"\n... y {len(data['errores']) - 3} más"
                frame_info['errors'].config(text=errores_text)
                frame_info['frame'].config(bg="#FF6B6B")
                frame_info['status'].config(background="#FF6B6B")
                frame_info['errors'].config(background="#FF6B6B")
                frame_info['label'].config(background="#FF6B6B")
                
            else:
                frame_info['status'].config(text="✓ Sin errores", foreground="#228B22", font=("Arial", 11, "bold"))
                frame_info['errors'].config(text=f"Archivo: {data['archivo']}" if data['archivo'] else "")
                frame_info['frame'].config(bg=self.COLOR_OK)
                frame_info['status'].config(background=self.COLOR_OK)
                frame_info['errors'].config(background=self.COLOR_OK)
                frame_info['label'].config(background=self.COLOR_OK)

        backups_found = sum(1 for d in self.backup_data.values() if d['tiene_backup'])
        partial_count = sum(1 for d in self.backup_data.values() if d.get('es_parcial'))
        real_errors_count = sum(1 for d in self.backup_data.values() if d['errores'] and not d.get('es_parcial'))
        
        if backups_found == 0:
            self.status_label.config(text="⚠ No se encontraron backups", foreground="red")
        elif real_errors_count > 0:
            self.status_label.config(text=f"✗ {real_errors_count} backup(s) con error(es) real(es)", foreground="red")
        elif partial_count > 0:
            self.status_label.config(text=f"⚠ {partial_count} backup(s) parcial(es)", foreground="#B8860B")
        else:
            self.status_label.config(text="✓ Todos los backups OK", foreground="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupMonitorGUI(root)
    root.mainloop()
