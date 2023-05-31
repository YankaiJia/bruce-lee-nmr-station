import pickle, pprint

import PySimpleGUI as sg

# Define the layout of the GUI
layout = [[sg.Text('Select a file to open:')],
          [sg.Input(key='-FILE-', enable_events=True, visible=False),
           sg.FileBrowse('Browse')],
          [sg.Button('Open'), sg.Button('Cancel')]]

# Create the window
window = sg.Window('File Selector', layout, size=(300, 100))

# Event loop to process events and get user input
while True:
    event, values = window.read()

    # If user closes window or clicks Cancel button, exit the program
    if event == sg.WIN_CLOSED or event == 'Cancel':
        file_path = None
        break

    # If user clicks Open button, return the path of the selected file
    if event == 'Open':
        file_path = values['-FILE-']
        break

# Close the window
window.close()

# Print the path of the selected file
if file_path is not None:
    print(f'Selected file: {file_path}')
else:
    print('No file selected.')


# load the pickle file and display the data
def load_pickle_file(file_path):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data.__dict__)

load_pickle_file(file_path)