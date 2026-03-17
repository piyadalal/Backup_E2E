import Tkinter as tk
from Tkinter import messagebox

# A sample method that returns some result
def calculate_result():
    result = 42  # Replace with your actual method logic
    return result

# Function to show the result in a popup
def show_popup():
    result = calculate_result()  # Call your method here
    # Display the result in a message box
    messagebox.showinfo("Result", "The result is: {%s}".format(result))

# Main Tkinter setup
def main():
    # Create the main window (it's not shown)
    root = tk.Tk()
    root.withdraw()  # Hide the main window (we only want the popup)

    # Show the popup with the result
    show_popup()

# Run the main function
if __name__ == "__main__":
    main()
