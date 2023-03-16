import tkinter as tk
from tkinter import ttk
import threading
from src.raspberry_camera import take_picture, listbox_select, sync_pictures, load_latest_picture, connect_to_pi


# GUI
root = tk.Tk()
root.title("Raspberry Pi Camera")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(row=0, column=0)


take_picture_button = ttk.Button(mainframe, text="Take Picture", command=take_picture)
ssh = connect_to_pi()
take_picture_button.config(command=lambda: take_picture(picture_list, image_label, current_image, take_picture_button, ssh))
take_picture_button.grid(row=0, column=0, padx=(0, 10))

picture_list = tk.Listbox(mainframe, width=30, height=20)
picture_list.grid(row=1, column=0)
picture_list.bind("<<ListboxSelect>>", lambda event: listbox_select(event, picture_list, image_label, current_image))


image_label = ttk.Label(mainframe)
image_label.grid(row=1, column=1)

# Start the sync thread
sync_thread = threading.Thread(target=sync_pictures, args=(picture_list,), daemon=True)
sync_thread.start()

# Load the latest picture
current_image = None
current_image = load_latest_picture(picture_list, image_label, current_image)
# load_latest_picture(picture_list, image_label, current_image)


# Main loop
root.mainloop()
