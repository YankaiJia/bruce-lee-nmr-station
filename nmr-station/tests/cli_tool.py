import click
from pynput.keyboard import Listener, Key
# import keyboard

@click.command()
@click.argument('function_name')
@click.argument('params', nargs=-1)
def cli(function_name, params):
    # Get the method from the instance
    func = globals().get(function_name)

    # Check if it's callable (i.e., a method)
    if callable(func):
        func(params)

# add new functions as testing tool below 

def check_health(params):
    print("healthy", params)

def vert_move(params):
    unit_distance = int(params[0])
    print(f"move vertically by unit distance {unit_distance} mm")
    
    # print("Press the space bar to start")
    # keyboard.wait('space')
    
    with Listener(on_press=read_key) as listener:
        listener.join()

    direction_str = ""
    while True:
        # print(keyboard.read_key())
        
        if last_key == Key.esc:
            return 
        elif last_key == Key.up:
            direction_str = "u"
        elif last_key == Key.down:
            direction_str = "d"

def read_key(key):
    last_key = key

if __name__ == '__main__':
    last_key = None
    cli()
