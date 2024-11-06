from tkinter import ttk

def apply_styles(root):
    """Apply consistent styling to the application"""
    style = ttk.Style()
    
    # Configure common styles
    style.configure(
        "TLabel",
        padding=5,
        font=('Arial', 10)
    )
    
    style.configure(
        "TButton",
        padding=5,
        font=('Arial', 10)
    )
    
    style.configure(
        "TFrame",
        padding=5
    )
    
    style.configure(
        "TLabelframe",
        padding=5
    )
    
    style.configure(
        "TEntry",
        padding=5
    )
