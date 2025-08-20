#!/usr/bin/env python3
"""
Wrench PATH Setup Utility

This script adds Wrench to the system PATH, making it accessible from anywhere.
"""

import os
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import winreg

class PathSetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wrench Engine - PATH Setup")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Set window icon if exists
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(__file__), 'wrench.ico'))
        except:
            pass
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(
            main_frame,
            text="Wrench Engine PATH Setup",
            font=('Helvetica', 16, 'bold')
        )
        header.pack(pady=10)
        
        # License text
        license_frame = ttk.LabelFrame(main_frame, text="License Agreement", padding=10)
        license_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        license_text = """
        Wrench Engine - MIT License
        
        Copyright (c) 2023 Wrench Team
        
        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:
        
        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.
        
        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        """
        
        license_text_widget = tk.Text(
            license_frame,
            wrap=tk.WORD,
            height=12,
            padx=10,
            pady=10,
            font=('Consolas', 9)
        )
        license_text_widget.insert('1.0', license_text)
        license_text_widget.config(state=tk.DISABLED)
        license_text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Agreement checkbox
        self.agreed = tk.BooleanVar()
        agree_cb = ttk.Checkbutton(
            main_frame,
            text="I agree to the terms of the license agreement",
            variable=self.agreed
        )
        agree_cb.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        install_btn = ttk.Button(
            button_frame,
            text="Add to PATH",
            command=self.add_to_path,
            style='Accent.TButton'
        )
        install_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ttk.Button(
            button_frame,
            text="Remove from PATH",
            command=self.remove_from_path
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        )
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Apply modern theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply a modern theme to the application."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = '#f0f0f0'
        fg_color = '#333333'
        accent_color = '#0078d7'
        
        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', padding=5)
        style.configure('Accent.TButton', background=accent_color, foreground='white')
        
        # Configure scrollbar
        style.configure('Vertical.TScrollbar', background=bg_color, troughcolor='#e0e0e0')
    
    def is_admin(self):
        """Check if the script is running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def add_to_path(self):
        """Add Wrench to the system PATH."""
        if not self.agreed.get():
            messagebox.showerror("Error", "You must agree to the license agreement first.")
            return
        
        if not self.is_admin():
            messagebox.showerror(
                "Admin Required",
                "This operation requires administrator privileges. "
                "Please run this program as administrator."
            )
            return
        
        try:
            # Get the directory containing this script
            wrench_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Get current PATH from registry
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as registry:
                with winreg.OpenKey(
                    registry,
                    r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                    0, 
                    winreg.KEY_READ | winreg.KEY_WRITE
                ) as key:
                    # Get current PATH
                    try:
                        path_value, path_type = winreg.QueryValueEx(key, 'Path')
                    except WindowsError:
                        path_value = ''
                        path_type = winreg.REG_EXPAND_SZ
                    
                    # Add Wrench to PATH if not already there
                    paths = path_value.split(os.pathsep)
                    if wrench_dir not in paths:
                        paths.append(wrench_dir)
                        new_path = os.pathsep.join(paths)
                        winreg.SetValueEx(key, 'Path', 0, path_type, new_path)
                        
                        # Notify other processes of the change
                        ctypes.windll.user32.SendMessageW(
                            0xFFFF,  # HWND_BROADCAST
                            0x001A,  # WM_SETTINGCHANGE
                            0,
                            'Environment'
                        )
                        
                        self.status_var.set("Successfully added Wrench to PATH. Please restart your applications.")
                        messagebox.showinfo("Success", "Wrench has been added to the system PATH.")
                    else:
                        self.status_var.set("Wrench is already in the system PATH.")
                        messagebox.showinfo("Info", "Wrench is already in your system PATH.")
        
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to update PATH: {str(e)}")
    
    def remove_from_path(self):
        """Remove Wrench from the system PATH."""
        if not self.is_admin():
            messagebox.showerror(
                "Admin Required",
                "This operation requires administrator privileges. "
                "Please run this program as administrator."
            )
            return
        
        try:
            # Get the directory containing this script
            wrench_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Get current PATH from registry
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as registry:
                with winreg.OpenKey(
                    registry,
                    r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                    0, 
                    winreg.KEY_READ | winreg.KEY_WRITE
                ) as key:
                    # Get current PATH
                    try:
                        path_value, path_type = winreg.QueryValueEx(key, 'Path')
                    except WindowsError:
                        path_value = ''
                        path_type = winreg.REG_EXPAND_SZ
                    
                    # Remove Wrench from PATH if present
                    paths = path_value.split(os.pathsep)
                    if wrench_dir in paths:
                        paths.remove(wrench_dir)
                        new_path = os.pathsep.join(paths)
                        winreg.SetValueEx(key, 'Path', 0, path_type, new_path)
                        
                        # Notify other processes of the change
                        ctypes.windll.user32.SendMessageW(
                            0xFFFF,  # HWND_BROADCAST
                            0x001A,  # WM_SETTINGCHANGE
                            0,
                            'Environment'
                        )
                        
                        self.status_var.set("Successfully removed Wrench from PATH.")
                        messagebox.showinfo("Success", "Wrench has been removed from the system PATH.")
                    else:
                        self.status_var.set("Wrench was not found in the system PATH.")
                        messagebox.showinfo("Info", "Wrench is not in your system PATH.")
        
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to update PATH: {str(e)}")

def main():
    # Check if running on Windows
    if not sys.platform.startswith('win'):
        print("Error: This setup utility is only available on Windows.")
        return 1
    
    # Create and run the application
    root = tk.Tk()
    app = PathSetupApp(root)
    root.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
