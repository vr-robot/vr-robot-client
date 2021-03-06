import cv2  # pip3 install opencv-python
import websockets  # pip3 install websockets
import base64
import asyncio
import json
import sys
import time

# get the camera
cam = cv2.VideoCapture(0)

# get the url of the socket server
if len(sys.argv) != 2:
    print('API_URL argument required')
    exit(1)

url = sys.argv[1]


# rate limit how frequently frames are sent
def current_milli_time():
    return round(time.time() * 1000)


MAX_FPS = 30
MAX_TIME_PER_FRAME = round(1000 / MAX_FPS)


# main method
async def main_camera():
    last_frame_sent_time = current_milli_time()

    while True:
        try:
            async with websockets.connect(url) as websocket:
                print('camera connected to %s server...' % (url))

                while True:
                    if current_milli_time() - last_frame_sent_time < MAX_TIME_PER_FRAME:
                        continue

                    # print('sending frame')

                    last_frame_sent_time = current_milli_time()

                    # get webcam frame
                    ret, frame = cam.read()

                    # scale down image so unity does not die when decoding it
                    scale_percent = 30  # percent of original size
                    width = int(frame.shape[1] * scale_percent / 100)
                    height = int(frame.shape[0] * scale_percent / 100)
                    dim = (width, height)
                    resized_frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

                    if not ret:
                        print("failed to grab frame")
                        break

                    # uncomment to show window:
                    # cv2.imshow("camera", resized_frame)

                    # convert frame to base 64 image
                    retval, buffer = cv2.imencode('.jpg', resized_frame)
                    base64_img_string = str(base64.b64encode(buffer.tobytes()))[2: -1]

                    # uncomment to view base64 string being printed
                    # print(base64_img_string)

                    # send image to socket server
                    data = {
                        "sender": "camera",
                        "data": base64_img_string
                    }

                    data_str = str(json.dumps(data))

                    # print(data_str)

                    await websocket.send(data_str)
        except:
            print('reconnecting to %s server...' % (url))
            time.sleep(3)

    cam.release()
    cv2.destroyAllWindows()


asyncio.get_event_loop().run_until_complete(main_camera())
