import requests
import sys
import time
import colorsys

def color_to_32bit(r, g, b):
    """Convert RGB values to a 32-bit color value."""
    return (r << 16) | (g << 8) | b

def generate_flash_frame(num_leds, color):
    """Generate a single color frame where all pixels are the same color."""
    return [{'index': i, 'color': color} for i in range(num_leds)]

def generate_rainbow_frame(num_leds, white_dot_index):
    """Generate a rainbow frame with a white dot moving across the strip."""
    frame = []
    for i in range(num_leds):
        # Calculate the hue for the rainbow cycle
        hue = (i + time.time() * 10) % 360 / 360.0
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        color = color_to_32bit(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        
        if i == white_dot_index:
            color = color_to_32bit(255, 255, 255)  # White color
        
        frame.append({'index': i, 'color': color})
    
    return frame

def send_frame_to_pi(frame_data):
    """Send a frame of LED data to the Raspberry Pi."""
    try:
        raspberry_pi_ip = '192.168.1.152'  # Raspberry Pi's IP address
        requests.post(f'http://{raspberry_pi_ip}:5000/update_leds', json={'leds': frame_data})
    except requests.RequestException:
        pass  # Ignore any connection errors

def run_flash_animation():
    num_leds = 397
    print("Running flash animation...")  # Initial message

    white_dot_index = 0  # Initial position of the white dot

    try:
        while True:
            # Generate and send the rainbow frame with the white dot
            frame_data = generate_rainbow_frame(num_leds, white_dot_index)
            send_frame_to_pi(frame_data)

            # Update the white dot position
            white_dot_index = (white_dot_index + 1) % num_leds

            # Calculate FPS
            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time >= 1.0:  # Every second
                fps = frame_count / elapsed_time
                print('\rFPS: {:.2f}'.format(fps), end='')
                frame_count = 0
                start_time = current_time
            else:
                frame_count += 1

            time.sleep(0.1)  # Adjust sleep time as needed

    except KeyboardInterrupt:
        print("\nTerminating program...")
        turn_off_all_leds()
        sys.exit(0)  # Exit the program gracefully

if __name__ == '__main__':
    start_time = time.time()
    frame_count = 0
    run_flash_animation()
