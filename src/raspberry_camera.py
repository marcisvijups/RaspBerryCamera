import os
import time
from datetime import datetime
import paramiko
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError
from src.config import RASPBERRY_PI_IP, RASPBERRY_PI_USERNAME, PRIVATE_KEY_PATH, LOCAL_PICTURE_DIR, IMAGE_SIZE


def take_picture(picture_list, image_label, current_image, take_picture_button, ssh):
    take_picture_button.config(state=tk.DISABLED)

    remote_directory = get_remote_directory()
    ssh.exec_command(f"mkdir -p {remote_directory}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"photo_{timestamp}.jpg"
    remote_path = f"{remote_directory}/{file_name}"

    # Wait for the raspistill command to complete
    _, stdout, _ = ssh.exec_command(f"raspistill -o {remote_path}")
    stdout.channel.recv_exit_status()

    local_directory = get_local_directory()
    os.makedirs(local_directory, exist_ok=True)
    local_path = f"{local_directory}/{file_name}"

    sftp = ssh.open_sftp()  # Open a SFTP session
    print(f"Remote path: {remote_path}")
    print(f"Local path: {local_path}")
    sftp.get(remote_path, local_path)
    sftp.close()

    add_picture_to_listbox(picture_list, file_name)
    display_picture(local_path, image_label, current_image)

    take_picture_button.config(state=tk.NORMAL)


def update_picture_list(picture_list):
    picture_list.delete(0, tk.END)

    files = []
    for root, _, file_names in os.walk(LOCAL_PICTURE_DIR):
        for file_name in file_names:
            if file_name.endswith(".jpg"):
                relative_path = os.path.relpath(root, LOCAL_PICTURE_DIR)
                files.append(os.path.join(relative_path, file_name))

    # Sort the files by modification time, with the newest at the top
    files.sort(key=lambda f: os.path.getmtime(os.path.join(LOCAL_PICTURE_DIR, f)), reverse=True)

    for file in files:
        picture_list.insert(tk.END, file)


def display_picture(file_path, image_label, current_image):
    try:
        image = Image.open(file_path)
    except UnidentifiedImageError:
        print(f"Error: Unable to open image '{file_path}'. The file might be corrupted or incomplete.")
        return

    image.thumbnail(IMAGE_SIZE)
    photo = ImageTk.PhotoImage(image)
    image_label.config(image=photo)
    image_label.image = photo
    return photo


def listbox_select(event, picture_list, image_label, current_image):
    selection = picture_list.curselection()
    if selection:
        selected_file = picture_list.get(selection[0])
        current_image = display_picture(os.path.join(LOCAL_PICTURE_DIR, selected_file), image_label, current_image)


def load_latest_picture(picture_list, image_label, current_image):
    files = []
    for root, _, filenames in os.walk(LOCAL_PICTURE_DIR):
        for filename in filenames:
            if filename.endswith(".jpg"):
                files.append(os.path.join(root, filename))

    if not files:
        return

    # Sort the files by modification time, with the newest at the top
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

    latest_file = files[0]
    display_picture(latest_file, image_label, current_image)

    # Find the index of the latest picture in the Listbox and select it
    index = 0
    for i in range(picture_list.size()):
        if picture_list.get(i) == os.path.relpath(latest_file, LOCAL_PICTURE_DIR):
            index = i
            break

    picture_list.selection_clear(0, tk.END)
    picture_list.selection_set(index)
    picture_list.activate(index)
    picture_list.see(index)
    current_image = display_picture(latest_file, image_label, current_image)
    return current_image


def sync_pictures(picture_list):
    while True:
        update_picture_list(picture_list)
        time.sleep(10)


def connect_to_pi():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    expanded_key_path = os.path.expanduser(PRIVATE_KEY_PATH)
    ssh.connect(RASPBERRY_PI_IP, username=RASPBERRY_PI_USERNAME, key_filename=expanded_key_path)
    return ssh


def get_remote_directory():
    today = datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    return f"/home/pi/pictures/{year}/{month}"


def get_local_directory():
    today = datetime.now()
    year = today.year
    month = today.month

    local_directory = os.path.join(LOCAL_PICTURE_DIR, f"{year:04d}/{month:02d}")
    return local_directory


def add_picture_to_listbox(picture_list, file_name):
    relative_path = os.path.relpath(get_local_directory(), LOCAL_PICTURE_DIR)
    picture_list.insert(tk.END, os.path.join(relative_path, file_name))
