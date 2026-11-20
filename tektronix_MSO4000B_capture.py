import pyvisa
import time
import re
import subprocess
import os
from datetime import datetime

def main():
    rm = pyvisa.ResourceManager()
    resource_list=rm.list_resources()
    print("\nresource list:")
    print(resource_list)
    for resource_num, resource_name in enumerate(resource_list):
        if resource_name.startswith("USB"):
            break
    else:
        print("*"*100+"\nERROR: instrument not found\n"+"*"*100)
        return -1


    scope =rm.open_resource(resource_list[resource_num])
    scope.timeout = 20000  # Set timeout to 20s for image capture and file transfer
    print("\nscope name:")
    idn_val=scope.query("*IDN?")
    print(idn_val)
    time.sleep(1)

    labels={
            "ch1":"SCL",
            "ch2":"SDA",
            "ch3":"U5 C1+",
            "ch4":"drvBrd current",
            "ch5":"",
            "ch6":"",
            "ch7":"",
            "ch8":"",
           }
    
    if "MSO66B" in idn_val:
        MSO66B(scope, labels)
    else:
        MSO4000B(scope, labels)

def MSO66B(scope, labels):
    pass

def MSO4000B(scope, labels):
    # scope.write('FACtory') #reset scope

    scope.write(f'CH1:LABel "{labels["ch1"]}"')
    time.sleep(.1)
    scope.write(f'CH2:LABel "{labels["ch2"]}"')
    time.sleep(.1)
    scope.write(f'CH3:LABel "{labels["ch3"]}"')
    time.sleep(.1)
    scope.write(f'CH4:LABel "{labels["ch4"]}"')
    time.sleep(.1)

    # delete_images(scope)
    screenshot_to_clipboard(scope)

    print("DONE!")

def screenshot_to_clipboard(scope):
    target_file='/Users/arthurschiro/Downloads/from_scope.png'
    capture_screenshot(scope,target_file)
    copy_image_to_clipboard(target_file)

def capture_screenshot(scope,target_file):
    # Query current working directory to identify the active USB drive (e.g. E: or F:)
    scope.write('FILESystem:CWD ""')
    time.sleep(0.2)
    cwd = scope.query('FILESystem:CWD?').strip().strip('"')
    print(f"Scope active drive / CWD: {cwd}")

    if cwd and len(cwd) >= 2 and cwd[1] == ':':
        drive = cwd.rstrip('/') + '/'
    else:
        # Default fallback if CWD query did not return a drive letter
        drive = 'E:/'

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{drive}image_capture_{timestamp}.png"

    print(f"Saving image to scope: {save_name}...")
    scope.write(f'SAVe:IMAGe "{save_name}"')

    # Wait for the scope to finish writing the file before reading it
    # SAVe:IMAGe is asynchronous and takes several seconds on USB drives
    opc = scope.query('*OPC?').strip()

    # Check for any scope execution errors
    err = scope.query('ALLEV?').strip()
    if err and not err.startswith('0'):
        print(f"Scope event log: {err}")

    # Read image from scope to computer
    cmd = f'FILESystem:READFile "{save_name}"'
    print(cmd)
    scope.write(cmd)
    time.sleep(.1)

    # Save image to known location
    img_raw = scope.read_raw()

    # Strip IEEE 488.2 block header if present
    png_start = img_raw.find(b'\x89PNG')
    img_bytes = img_raw[png_start:] if png_start != -1 else img_raw

    with open(target_file, 'wb') as target:
        target.write(img_bytes)

    print(f"Screenshot saved to {target_file} ({len(img_bytes)} bytes)")

    # Clean up temporary file from scope drive
    try:
        scope.write(f'FILESystem:DELETe "{save_name}"')
    except Exception:
        pass

def copy_image_to_clipboard(target_file):
    file_save2clipboard = 'set the clipboard to (read (POSIX file "'+str(target_file)+'") as JPEG picture)'
    subprocess.run(["osascript", "-e", file_save2clipboard])

def get_image_list(scope):
    scope.write('FILESystem:CWD ""') # scope diddn't see flash drive until this was called.
    time.sleep(.1)

    dir_str=scope.query("FILESystem:DIR?")
    time.sleep(.1)
    print("\nfiles in cwd")
    print(dir_str)
    pass

    dir_list=dir_str.split('"')
    image_list=[]
    for file_name in dir_list:
        if file_name.endswith(".png"):
            image_list.append(file_name)

    print("\nimages in cwd:")
    print(image_list)

    return image_list

def delete_images(scope):

    image_list=get_image_list(scope)

    for filename in image_list:
        cmd=f'FILESystem:DELETe "{filename}"'
        print(cmd)
        scope.write(cmd)

    image_list=get_image_list(scope)
    pass

    return image_list
if __name__ == "__main__":
    main()