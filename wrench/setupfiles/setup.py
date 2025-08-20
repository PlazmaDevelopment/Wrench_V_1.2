#!/usr/bin/env python3
"""
Wrench Engine Setup Wizard

This script provides a graphical interface for installing Wrench Engine.
"""

import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import ctypes
import json
from pathlib import Path

class SetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Wrench Engine Setup")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Set window icon if exists
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(__file__), 'wrench.ico'))
        except:
            pass
        
        # Setup data
        self.install_path = os.path.join(os.path.expanduser('~'), 'WrenchEngine')
        self.components = {
            'core': {'name': 'Core Engine', 'required': True, 'installed': True, 'size': '50 MB'},
            'templates': {'name': 'Project Templates', 'required': False, 'installed': True, 'size': '20 MB'},
            'examples': {'name': 'Example Projects', 'required': False, 'installed': True, 'size': '100 MB'},
            'docs': {'name': 'Documentation', 'required': False, 'installed': True, 'size': '15 MB'},
        }
        
        # Setup options
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.add_to_path = tk.BooleanVar(value=True)
        
        self.current_step = 0
        self.steps = [
            self.create_welcome_page,
            self.create_license_page,
            self.create_install_location_page,
            self.create_components_page,
            self.create_ready_page,
            self.create_installing_page,
            self.create_finish_page
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header = ttk.Label(
            self.main_frame,
            text="Wrench Engine Setup",
            font=('Helvetica', 16, 'bold')
        )
        self.header.pack(pady=(0, 20))
        
        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient=tk.HORIZONTAL,
            mode='determinate',
            length=760
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.back_btn = ttk.Button(
            self.button_frame,
            text="< Back",
            command=self.previous_step,
            state=tk.DISABLED
        )
        self.back_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(
            self.button_frame,
            text="Next >",
            command=self.next_step,
            style='Accent.TButton'
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(
            self.button_frame,
            text="Cancel",
            command=self.confirm_exit
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Apply theme
        self.apply_theme()
        
        # Show first step
        self.show_step(0)
    
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
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color)
        style.configure('TCheckbutton', background=bg_color)
        style.configure('TRadiobutton', background=bg_color)
    
    def clear_content(self):
        """Clear the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_step(self, step):
        """Show the specified step."""
        self.current_step = step
        self.clear_content()
        self.steps[step]()
        
        # Update progress
        progress = int((step / (len(self.steps) - 1)) * 100)
        self.progress_bar['value'] = progress
        
        # Update buttons
        self.back_btn['state'] = tk.NORMAL if step > 0 else tk.DISABLED
        
        if step == len(self.steps) - 1:
            self.next_btn['text'] = 'Finish'
            self.next_btn['command'] = self.finish_installation
        else:
            self.next_btn['text'] = 'Next >'
            self.next_btn['command'] = self.next_step
    
    def next_step(self):
        """Proceed to the next step."""
        if self.current_step < len(self.steps) - 1:
            # Validate current step before proceeding
            if self.validate_step(self.current_step):
                self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Return to the previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def validate_step(self, step):
        """Validate the current step before proceeding."""
        if step == 1:  # License agreement
            if not hasattr(self, 'license_accepted') or not self.license_accepted.get():
                messagebox.showerror("Error", "You must accept the license agreement to continue.")
                return False
        elif step == 2:  # Install location
            path = self.install_path_var.get().strip()
            if not path:
                messagebox.showerror("Error", "Please specify an installation directory.")
                return False
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot create directory: {str(e)}")
                    return False
        return True
    
    def create_welcome_page(self):
        """Create the welcome page."""
        welcome_text = (
            "Welcome to the Wrench Engine Setup Wizard\n\n"
            "This will install Wrench Engine on your computer.\n"
            "It is recommended that you close all other applications before continuing.\n\n"
            "Click Next to continue, or Cancel to exit the Setup Wizard."
        )
        
        ttk.Label(
            self.content_frame,
            text=welcome_text,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=20)
    
    def create_license_page(self):
        """Create the license agreement page."""
        license_frame = ttk.LabelFrame(self.content_frame, text="License Agreement")
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
            height=15,
            padx=10,
            pady=10,
            font=('Consolas', 9)
        )
        license_text_widget.insert('1.0', license_text)
        license_text_widget.config(state=tk.DISABLED)
        license_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Agreement checkbox
        self.license_accepted = tk.BooleanVar()
        ttk.Checkbutton(
            self.content_frame,
            text="I accept the terms of the license agreement",
            variable=self.license_accepted
        ).pack(pady=10)
    
    def create_install_location_page(self):
        """Create the installation location page."""
        ttk.Label(
            self.content_frame,
            text="Choose the folder in which to install Wrench Engine:",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(10, 5))
        
        # Install location frame
        location_frame = ttk.Frame(self.content_frame)
        location_frame.pack(fill=tk.X, pady=10)
        
        self.install_path_var = tk.StringVar(value=self.install_path)
        
        ttk.Entry(
            location_frame,
            textvariable=self.install_path_var,
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            location_frame,
            text="Browse...",
            command=self.browse_install_location
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Disk space info
        disk_info = ttk.LabelFrame(self.content_frame, text="Disk Space Requirements")
        disk_info.pack(fill=tk.X, pady=10)
        
        # Calculate required space
        required_space = sum(
            int(comp['size'].split()[0]) 
            for comp in self.components.values() 
            if comp['installed']
        )
        
        # Get disk free space
        try:
            total, used, free = shutil.disk_usage(os.path.splitdrive(self.install_path)[0])
            free_gb = free // (2**30)
            status = f"Required: {required_space} MB | Available: {free_gb} GB"
            status_color = 'green' if (free_gb * 1024) > required_space else 'red'
        except:
            status = "Required: {} MB | Available: Unknown".format(required_space)
            status_color = 'black'
        
        ttk.Label(
            disk_info,
            text=status,
            foreground=status_color
        ).pack(pady=5)
    
    def create_components_page(self):
        """Create the components selection page."""
        ttk.Label(
            self.content_frame,
            text="Select the components you want to install:",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 10))
        
        components_frame = ttk.LabelFrame(self.content_frame, text="Components")
        components_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create checkboxes for each component
        for comp_id, comp in self.components.items():
            if comp['required']:
                # For required components, show a label instead of a checkbox
                frame = ttk.Frame(components_frame)
                frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(
                    frame,
                    text=f"{comp['name']} (Required)",
                    width=30,
                    anchor=tk.W
                ).pack(side=tk.LEFT)
                
                ttk.Label(
                    frame,
                    text=comp['size'],
                    width=10,
                    anchor=tk.W
                ).pack(side=tk.LEFT)
            else:
                # For optional components, show a checkbox
                var = tk.BooleanVar(value=comp['installed'])
                comp['var'] = var
                
                frame = ttk.Frame(components_frame)
                frame.pack(fill=tk.X, pady=2)
                
                cb = ttk.Checkbutton(
                    frame,
                    text=comp['name'],
                    variable=var,
                    command=lambda cid=comp_id: self.update_component(cid)
                )
                cb.pack(side=tk.LEFT, anchor=tk.W)
                
                ttk.Label(
                    frame,
                    text=comp['size'],
                    width=10
                ).pack(side=tk.RIGHT)
    
    def create_ready_page(self):
        """Create the ready to install page."""
        ttk.Label(
            self.content_frame,
            text="Setup is now ready to install Wrench Engine on your computer.",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(10, 20))
        
        # Installation summary
        summary = ttk.LabelFrame(self.content_frame, text="Installation Summary")
        summary.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Install location
        ttk.Label(
            summary,
            text=f"Destination Location:\n{self.install_path_var.get()}",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
        
        # Selected components
        components_text = "Selected Components:\n"
        for comp_id, comp in self.components.items():
            if comp['required'] or comp['installed']:
                components_text += f"- {comp['name']} ({comp['size']})\n"
        
        ttk.Label(
            summary,
            text=components_text,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
        
        # Space requirements
        required_space = sum(
            int(comp['size'].split()[0]) 
            for comp in self.components.values() 
            if comp['installed']
        )
        
        ttk.Label(
            summary,
            text=f"Total Space Required: {required_space} MB",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
    
    def create_installing_page(self):
        """Create the installation progress page."""
        self.install_path = self.install_path_var.get()
        
        # Update components based on user selection
        for comp_id, comp in self.components.items():
            if not comp['required']:
                comp['installed'] = comp['var'].get()
        
        ttk.Label(
            self.content_frame,
            text="Installing Wrench Engine. Please wait...",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(10, 20))
        
        # Progress frame
        self.progress_frame = ttk.Frame(self.content_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="Preparing installation...",
            justify=tk.LEFT
        )
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.content_frame, text="Installation Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            height=10,
            padx=5,
            pady=5,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Start installation in a separate thread
        self.root.after(100, self.perform_installation)
    
    def create_finish_page(self):
        """Create the installation complete page."""
        ttk.Label(
            self.content_frame,
            text="Wrench Engine has been successfully installed on your computer.",
            justify=tk.LEFT,
            font=('Helvetica', 10, 'bold')
        ).pack(anchor=tk.W, pady=(20, 10))
        
        # Options frame
        options_frame = ttk.LabelFrame(self.content_frame, text="Options")
        options_frame.pack(fill=tk.X, pady=10)
        
        self.launch_wrench = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Launch Wrench Engine",
            variable=self.launch_wrench
        ).pack(anchor=tk.W, pady=2)
        
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Create desktop shortcut",
            variable=self.create_desktop_shortcut
        ).pack(anchor=tk.W, pady=2)
        
        self.add_to_path = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Add Wrench to system PATH",
            variable=self.add_to_path
        ).pack(anchor=tk.W, pady=2)
        
        # Installation log
        log_frame = ttk.LabelFrame(self.content_frame, text="Installation Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            height=8,
            padx=5,
            pady=5,
            state=tk.DISABLED
        )
        log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add log messages
        log_text.config(state=tk.NORMAL)
        log_text.insert(tk.END, "Installation completed successfully!\n\n")
        log_text.insert(tk.END, f"Wrench Engine has been installed to:\n{self.install_path}\n\n")
        log_text.insert(tk.END, "You can now create and run Wrench projects.")
        log_text.config(state=tk.DISABLED)
    
    def browse_install_location(self):
        """Open a directory selection dialog."""
        path = filedialog.askdirectory(
            title="Select Installation Directory",
            mustexist=False
        )
        
        if path:
            self.install_path_var.set(path)
    
    def update_component(self, component_id):
        """Update the installation status of a component."""
        self.components[component_id]['installed'] = self.components[component_id]['var'].get()
    
    def log_message(self, message):
        """Add a message to the installation log."""
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.root.update_idletasks()
    
    def update_progress(self, value, message=None):
        """Update the progress bar and status message."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = value
            
        if message and hasattr(self, 'progress_label'):
            self.progress_label.config(text=message)
            
        self.root.update_idletasks()
    
    def perform_installation(self):
        """Perform the actual installation process."""
        try:
            self.log_message("Starting installation...")
            self.update_progress(10, "Preparing installation...")
            
            # Create installation directory
            install_dir = self.install_path_var.get()
            os.makedirs(install_dir, exist_ok=True)
            self.log_message(f"Installation directory: {install_dir}")
            
            # Simulate file copying (replace with actual installation logic)
            self.update_progress(20, "Copying files...")
            self.log_message("Copying core files...")
            
            # Copy core files
            source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.copy_directory(source_dir, install_dir)
            self.log_message("Core files copied successfully.")
            
            # Create shortcuts if needed
            if self.create_desktop_shortcut.get():
                self.update_progress(80, "Creating shortcuts...")
                self.create_shortcut(install_dir)
                self.log_message("Desktop shortcut created.")
            
            # Add to PATH if needed
            if self.add_to_path.get():
                self.update_progress(90, "Updating system PATH...")
                self.add_to_system_path(install_dir)
                self.log_message("Added to system PATH.")
            
            self.update_progress(100, "Installation complete!")
            self.log_message("Installation completed successfully!")
            
            # Move to the finish page
            self.root.after(1000, lambda: self.show_step(len(self.steps) - 1))
            
        except Exception as e:
            self.log_message(f"Error during installation: {str(e)}")
            messagebox.showerror("Installation Error", f"An error occurred during installation: {str(e)}")
    
    def copy_directory(self, src, dst):
        """Copy a directory recursively."""
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            
            # Skip some directories and files
            if os.path.basename(s) in ['.git', '__pycache__', '.gitignore', '.gitattributes']:
                continue
                
            if os.path.isdir(s):
                self.copy_directory(s, d)
            else:
                shutil.copy2(s, d)
    
    def create_shortcut(self, install_dir):
        """Create a desktop shortcut."""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Wrench Engine.lnk")
            target = os.path.join(install_dir, "wrench", "main.py")
            w_dir = os.path.join(install_dir, "wrench")
            icon = os.path.join(install_dir, "wrench", "assets", "icon.ico")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = f'"{target}"'
            shortcut.WorkingDirectory = w_dir
            shortcut.IconLocation = icon
            shortcut.save()
            
        except Exception as e:
            self.log_message(f"Warning: Could not create desktop shortcut: {str(e)}")
    
    def add_to_system_path(self, install_dir):
        """Add Wrench to the system PATH."""
        try:
            import winreg
            
            # Get the current PATH
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as registry:
                with winreg.OpenKey(
                    registry,
                    r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                    0, 
                    winreg.KEY_READ | winreg.KEY_WRITE
                ) as key:
                    try:
                        path_value, path_type = winreg.QueryValueEx(key, 'Path')
                    except WindowsError:
                        path_value = ''
                        path_type = winreg.REG_EXPAND_SZ
                    
                    # Add Wrench to PATH if not already there
                    paths = path_value.split(os.pathsep)
                    if install_dir not in paths:
                        paths.append(install_dir)
                        new_path = os.pathsep.join(paths)
                        winreg.SetValueEx(key, 'Path', 0, path_type, new_path)
                        
                        # Notify other processes of the change
                        ctypes.windll.user32.SendMessageW(
                            0xFFFF,  # HWND_BROADCAST
                            0x001A,  # WM_SETTINGCHANGE
                            0,
                            'Environment'
                        )
        except Exception as e:
            self.log_message(f"Warning: Could not add to system PATH: {str(e)}")
    
    def finish_installation(self):
        """Finish the installation process."""
        # Launch Wrench if selected
        if hasattr(self, 'launch_wrench') and self.launch_wrench.get():
            try:
                wrench_exe = os.path.join(self.install_path, "wrench", "main.py")
                subprocess.Popen([sys.executable, wrench_exe])
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch Wrench Engine: {str(e)}")
        
        self.root.quit()
    
    def confirm_exit(self):
        """Confirm before exiting the installer."""
        if messagebox.askyesno("Exit Setup", "Are you sure you want to cancel the installation?"):
            self.root.quit()

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Check if running on Windows
    if not sys.platform.startswith('win'):
        print("Error: This installer is only available on Windows.")
        return 1
    
    # Check for admin rights
    if not is_admin():
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return 0
    
    # Create and run the installer
    root = tk.Tk()
    app = SetupWizard(root)
    root.mainloop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
