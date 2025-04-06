import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import os
from pathlib import Path
import threading


project_folder = Path(__file__).resolve().parents[0]

temporal_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Temporal Zone'
persistent_folder_path = project_folder / 'Data Management' / 'Landing Zone' / 'Persistent Zone'

# Importing the functions from the Fist Part of the project
from Python.Data_Management.Data_Ingestion.Streaming_Ingestion.Warm_path import kafka_redis_consumer_warm_path
from Python.Data_Management.Landing_Zone import create_folders, transfer_data_to_delta_lake

from Python.Data_Management.Data_Ingestion.Batch_Ingestion import imbd_ingestion, boxoffice_ingestion, ml_20m_ingestion
from Python.Data_Management.Data_Ingestion.Streaming_Ingestion.Hot_path import kafka_consumer_hot_path, kafka_producer_hot_path
from Python.Data_Management.Data_Ingestion.Streaming_Ingestion.Warm_path import kafka_producer_warm_path, kafka_redis_consumer_warm_path

#Importing others functions
from Python.Monitoring.monitor import start_monitoring_thread, stop_monitoring_thread
from Python.Code_Quality import check_code_quality


def write_to_terminal(message):
    terminal_text.config(state=tk.NORMAL)  # Enable text widget to insert new text
    terminal_text.insert(tk.END, message + "\n")
    terminal_text.see(tk.END)  # Automatically scroll to the bottom
    terminal_text.config(state=tk.DISABLED)  # Disable editing again
    root.update()

def write_to_terminal2(message):
    terminal_text2.config(state=tk.NORMAL)
    terminal_text2.insert(tk.END, message + "\n")
    terminal_text2.see(tk.END)
    terminal_text2.config(state=tk.DISABLED)
    root.update()
    
    
def button1_action():

    global monitor_active, monitor_thread
    if not monitor_active:
        write_to_terminal2("Monitoring process started...\n")
        monitor_thread = start_monitoring_thread(write_to_terminal2)  
        monitor_active = True
    else:
        messagebox.showinfo("Execution in progress", "The monitor is already in progress.")

    write_to_terminal("Creating Data Management folders ... !!!\n")
    try:
        create_folders.create_folders(project_folder)
    except Exception as e:
        write_to_terminal(f"Creation of Data Management foldes failed: {e}")
        return
    write_to_terminal("Successfully created Data Management folders !!!\n")

    write_to_terminal("Ingesting ml-20m dataset to Temporal folder ...")
    try:
        ml_20m_ingestion.ml_20m_dataset_ingestion(temporal_folder_path)
    except Exception as e:
        write_to_terminal(f"Failed to ingest ml-20 dataset to Temporal folder: {e}")
        return
    write_to_terminal("Successfully ingested ml-20m dataset to Temporal folder !!!")

    write_to_terminal("Ingesting IMBd dataset to Temporal folder ...")
    try:
        imbd_ingestion.imbd_ingestion(temporal_folder_path)
    except Exception as e:
        write_to_terminal(f"Failed to ingest IMBd dataset to Temporal folder: {e}")
        return
    write_to_terminal("Successfully ingested IMBd dataset to Temporal folder !!!")

    write_to_terminal("Ingesting boxOffice dataset to Temporal folder ...")
    try:
        boxoffice_ingestion.boxOffice_daily_ingestion(temporal_folder_path)
    except Exception as e:
        write_to_terminal(f"Failed to ingest boxOffice dataset to Temporal folder: {e}")
        return
    write_to_terminal("Successfully ingested boxOffice dataset to Temporal folder !!!")

    write_to_terminal("Transferring data to Persistent folder creating Delta Tables ...")
    try:
        transfer_data_to_delta_lake.create_delta_tables(temporal_folder_path, persistent_folder_path)
    except Exception as e:
        write_to_terminal(f"Failed to transfer data to Persistent folder and create Delta Table: {e}")
        return
    write_to_terminal("Successfully transferred data to Persistent folder and created Delta Table !!!")




def doCheckCodeQuality(secondary_terminal):
    
    secondary_terminal.config(state=tk.NORMAL)
    secondary_terminal.insert(tk.END, "Checking Code Quality...\n")
        
    code_quality = check_code_quality.run_flake8() 
    
    secondary_terminal.insert(tk.END, code_quality)
    secondary_terminal.insert(tk.END, "\n")
    secondary_terminal.insert(tk.END, "Finished checking code quality.")
    secondary_terminal.see(tk.END)
    secondary_terminal.config(state=tk.DISABLED)


# Open new window with code quality check
def button2_action():
    secondary_window = tk.Toplevel(root)
    secondary_window.title("Code Quality Check")
    secondary_window.geometry("600x500")

    label = tk.Label(secondary_window, font=("Arial", 16), text="Checking Code Quality...")
    label.place(relx=0.5, rely=0.05, anchor="center") # Centered at the top of the window


    secondary_terminal = tk.Text(secondary_window, bg="black", fg="white", font=("Courier", 10), wrap="word")
    secondary_terminal.place(relx=0.03, rely=0.15, relwidth=0.9, relheight=0.8)  # Fills most of the window

    secondary_window.after(500, lambda: doCheckCodeQuality(secondary_terminal))
     


def button3_action():
    producer_thread = threading.Thread(target=kafka_producer_hot_path.real_time_processing, daemon=True)
    producer_thread.start()
    
    consumer_thread = threading.Thread(target=kafka_consumer_hot_path.receive_messages, daemon=True)
    consumer_thread.start()


def button4_action():
    producer_thread = threading.Thread(target=kafka_producer_warm_path.near_real_time_processing, daemon=True)
    producer_thread.start()
    
    consumer_thread = threading.Thread(target=kafka_redis_consumer_warm_path.receive_messages_minutely, daemon=True)
    consumer_thread.start()

# Create the main window
root = tk.Tk()
root.title("Data Management and Data Analysis")
# Get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set window dimensions to a percentage of the screen size 
window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)

# Center the window on the screen
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

start = False
monitor_thread = None 
monitor_active = False  

button1 = tk.Button(root, text="Start Batch Ingestion", command=button1_action, width=10, height=2, font=("Helvetica", 12))
button1.place(relx=0.01, rely=0.02, relwidth=0.16, relheight=0.1)

button2 = tk.Button(root, text="Check Code Quality", command=button2_action, width=10, height=2, font=("Helvetica", 12))
button2.place(relx=0.63, rely=0.02, relwidth=0.35, relheight=0.1)

button3 = tk.Button(root, text="Start Streaming Ingestion\n(Hot Path)", command=button3_action, width=10, height=2, font=("Helvetica", 12))
button3.place(relx=0.23, rely=0.02, relwidth=0.16, relheight=0.1)

button4 = tk.Button(root, text="Start Streaming Ingestion\n(Warm Path)", command=button4_action, width=10, height=2, font=("Helvetica", 12))
button4.place(relx=0.45, rely=0.02, relwidth=0.16, relheight=0.1)



# Create a Text widget to simulate the terminal output within the main window
terminal_text = tk.Text(root, bg="black", fg="white", font=("Courier", 10), wrap="word")
terminal_text.place(relx=0.01, rely=0.15, relwidth=0.60, relheight=0.83)  

terminal_text2 = tk.Text(root, bg="black", fg="white", font=("Courier", 10), wrap="word")
terminal_text2.place(relx=0.63, rely=0.15, relwidth=0.35, relheight=0.83)  
write_to_terminal("Click the 'Start Batch Ingestion' button to start the ingestion from various datasources :)\n")

# Make terminal read-only initially
terminal_text.config(state=tk.DISABLED)


# Start the main loop
root.mainloop()



