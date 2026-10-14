
import tkinter as tk
from tkinter import ttk


def main():
    # Create the main application window
    root = tk.Tk()
    root.title("ProjectPos_2026 - POS System")
    root.geometry("900x560")

    # Main content area
    main_frame = ttk.Frame(root, padding=30)
    main_frame.pack(fill="both", expand=True)

    # Title
    title_label = ttk.Label(
        main_frame,
        text="Supermarket POS System",
        font=("Arial", 22, "bold")
    )
    title_label.pack(pady=30)

    # Subtitle
    subtitle_label = ttk.Label(
        main_frame,
        text="Software Engineering Practice Assignment",
        font=("Arial", 12)
    )
    subtitle_label.pack(pady=10)

    # Sale button (not implemented yet)
    sale_button = ttk.Button(
        main_frame,
        text="Process Sale",
        state="disabled"
    )
    sale_button.pack(pady=20, ipadx=30, ipady=10)

    # Return button (not implemented yet)
    return_button = ttk.Button(
        main_frame,
        text="Handle Returns",
        state="disabled"
    )
    return_button.pack(pady=10, ipadx=30, ipady=10)

    # Status
    status_label = ttk.Label(
        main_frame,
        text="System Initialization Completed",
        font=("Arial", 10)
    )
    status_label.pack(pady=30)

    root.mainloop()


if __name__ == "__main__":
    main()
