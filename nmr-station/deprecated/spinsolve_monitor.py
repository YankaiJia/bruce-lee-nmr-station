import pyautogui
from pyautogui import (
    screenshot,
    locateOnScreen,
    ImageNotFoundException,
    click,
    typewrite,
)

# from PIL import Image

from datetime import datetime
import time


def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"Execution time: {end_time - start_time}")
        return result

    return wrapper


@measure_execution_time
def screenshot_all_slot_buttons():
    x0, y0 = 12, 187
    button_width, button_height = 104, 69
    dx, dy = 128, 0

    for i in range(20):
        image_name = (
            "./images/references/button_"
            + ("0" if i < 9 else "")
            + str(i + 1)
            + "_yellow"
            + ".png"
        )
        # image_name = "./images/current_status/button_" + ("0" if i < 9 else "") + str(i + 1) + ".png"
        button_left = x0 + i * dx
        button_top = y0 + i * dy

        screenshot(image_name, [button_left, button_top, button_width, button_height])


@measure_execution_time
def get_current_status():
    x0, y0 = 12, 187
    button_width, button_height = 104, 30
    dx, dy = 128, 0

    for i in range(20):

        image_name = (
            "./images/references/button_"
            + ("0" if i < 9 else "")
            + str(i + 1)
            + "_green"
            + ".png"
        )
        is_green = True
        try:
            locateOnScreen(image_name)
        except ImageNotFoundException:
            is_green = False

        print(f"Slot {i + 1}", ("Finished" if is_green == True else "Empty"))

        if is_green:
            click(x0 + i * dx, y0 + i * dy)

            click(21, 383)

            # wait until communication with auto sampler is complete

            time.sleep(1)


def add_sample_to_slot(
    slot_id: int, sample_text: str, solvent_text: str, custom_text: str = ""
):
    slot_id -= 1
    x0, y0 = 12, 187
    dx, dy = 128, 0
    click(x0 + slot_id * dx, y0 + slot_id * dy)

    # first text field - sample
    click(134, 298)
    typewrite(sample_text)
    # solvent text field
    click(134, 326)
    typewrite(solvent_text)
    # custom text field
    click(134, 354)
    typewrite(custom_text)

    # Add sample button
    click(21, 383)


@measure_execution_time
def remove_all_green_sample():
    pass


if __name__ == "__main__":
    # get_current_status()

    add_sample_to_slot(1, "Reference", "Unknown", "LGA")
    add_sample_to_slot(20, "Test 2", "Unknown")
