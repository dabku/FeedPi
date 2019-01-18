from .piycamera.PiyCamera.PiyCamera import OSDetector
from .piycamera.PiyCamera.CameraHelper import get_frame_mean, get_jpg_from_frame, create_blank_image_b, resize_image
import cv2
from datetime import datetime
import time
from os import path
from .movement import Movement

from numpy import ones, uint8, mean
import logging
if OSDetector.is_embedded():
    from .piycamera.PiyCamera.PiyCamera import PiCamera as PiyCamera
else:
    from .piycamera.PiyCamera.PiyCamera import PyCamera as PiyCamera

logger = logging.getLogger('vision')


class Vision:
    def __init__(self, settings):

        self.feed = PiyCamera()

        self.feed.start_camera_thread()

        # Defaults
        self.frame_res = self.downscaled_frame_res = [640, 480]
        #set max resolution
        # todo does not work on rpi
        self.feed.set_resolution(1920, 1080)
        self.noise_pass = False
        self.threshold = 50
        self.img_save_cooldown = 10
        self.vid_save_cooldown = 10

        self.movement = Movement(settings)
        self.apply_settings(settings)

        self.frame = ones((self.frame_res[1], self.frame_res[0], 3), uint8)
        self.downscaled_frame = ones((self.downscaled_frame_res[1], self.downscaled_frame_res[0], 3), uint8)

        self.refresh_feed()
        self.thresholded_frame = None
        self.gray_frames = [self.frame, self.frame, self.frame]

        self.ts_last_saved_img = time.time()

    def apply_settings(self, config):
        self.apply_camera_settings(config['camera'])
        self.movement.apply_settings(config)
        try:
            self.threshold = int(config['frame_threshold'])
            self.img_save_cooldown = int(config['image_saving_cooldown'])
            self.vid_save_cooldown = int(config['video_saving_cooldown'])
            self.noise_pass = (config['noise_pass'])
            self.frame_res = [int(config['camera']['camera_res'][0]),
                              int(config['camera']['camera_res'][1])]
            self.downscaled_frame_res = [int(config['camera']['movement_res'][0]),
                                         int(config['camera']['movement_res'][1])]
        except KeyError as e:
            logger.error('Configuration file incorrect {}'.format(e))

    def get_settings(self):
        movement_dict = self.movement.get_settings()
        camera = self.get_camera_settings()
        camera['movement_res'] = self.downscaled_frame_res
        return {'frame_threshold': self.threshold,
                'image_saving_cooldown': self.img_save_cooldown,
                'video_saving_cooldown': self.vid_save_cooldown,
                'noise_pass': self.noise_pass,
                **movement_dict,
                'camera': {**camera}}

    def get_camera_settings(self):
        return {
            'camera_res': self.feed.get_resolution(),
            'brightness': self.feed.get_brightness(),
            'contrast': self.feed.get_contrast(),
            'exposure': self.feed.get_exposure(),
            'fps': self.feed.get_fps(),
            'iso': self.feed.get_iso(),
            # 'shutter_speed': self.feed.get_shutter_speed()
        }

    def apply_camera_settings(self, config):
        self.feed.set_resolution(int(config['camera_res'][0]), int(config['camera_res'][1]))
        self.feed.set_brightness(int(config['brightness']))
        self.feed.set_contrast(int(config['contrast']))
        #todo maybe I will need shutter speed at some point
        self.feed.set_iso(int(config['iso']))

    def refresh_feed(self):
        self.frame = self.feed.read_frame()
        self.downscaled_frame = resize_image(self.frame, self.downscaled_frame_res[0], self.downscaled_frame_res[1])

    def refresh_gray_frames(self):
        if self.noise_pass:
            self.gray_frames[2] = self.gray_frames[1]
        self.gray_frames[1] = self.gray_frames[0]
        self.gray_frames[0] = cv2.cvtColor(self.downscaled_frame, cv2.COLOR_BGR2GRAY)

    def get_image_diff(self):
        """
        Gets image difference.
        :return: Frame with only black and white pixels
        """
        self.refresh_gray_frames()
        frame_delta = cv2.absdiff(self.gray_frames[0], self.gray_frames[1])
        if self.noise_pass:
            frame_delta2 = cv2.absdiff(self.gray_frames[1], self.gray_frames[2])
            frame_delta = cv2.bitwise_and(frame_delta, frame_delta2)
        self.thresholded_frame = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]

    def take_snap(self, output_dir):
        """
        Takes image if image save colldown is reached
        :param output_dir: Output directory
        """
        if time.time() - self.ts_last_saved_img > self.img_save_cooldown:
            self.ts_last_saved_img = time.time()
            filename = datetime.now().strftime('%Y%m%d%H_%M_%S') + '.png'
            self.feed.save_image(path.join(output_dir, filename))

    def get_movement_level(self):
        return self.movement.get_movement_level(self.thresholded_frame)

    @staticmethod
    def convert_to_jpg(frame):
        try:
            jpg = get_jpg_from_frame(frame)
        except Exception as e:
            jpg = get_jpg_from_frame(create_blank_image_b())
        return jpg



