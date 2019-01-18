from .piycamera.PiyCamera.CameraHelper import get_frame_mean, get_jpg_from_frame, create_blank_image_b, resize_image
import cv2
import time
import json
from .vision import Vision
import queue
import threading
import re
import os
import logging
import sys
import errno
from .zmqconnector.connector import Client

logger = logging.getLogger('feedpi')


class Discord:
    def __init__(self, config, inq, outq):
        self.discord_port = 5556
        self.discord_address = 'localhost'
        self.discord_cooldown = 1
        self.discord_enabled = True
        self.discord_on_demand = True
        self.discord_triggering = True
        self.discord_bot_comm_worker = None
        self.in_message_queue = inq
        self.out_message_queue = outq

        self.apply_config(config)

        self.zmq_client = Client(self.discord_port)
        self.start_worker()

    def apply_config(self, config_dict):
        try:
            ip = config_dict['server_address']
            if isip(ip):
                self.discord_address = ip
            else:
                logger.error('Discord address is not an IP: {}'.format(ip))
            try:
                port = int(config_dict['comm_port'])
                self.discord_port = port
            except ValueError:
                logger.error('Discord port is not an int: {}'.format(config_dict['comm_port']))

            self.discord_cooldown = config_dict['cooldown']
            self.discord_enabled = config_dict['enabled']
            self.discord_on_demand = config_dict['on_demand']
            self.discord_triggering = config_dict['triggering']
        except KeyError as e:
            logger.error('Discord configuration file section is incorrect {}'.format(e))
            raise ConfigurationError
        except ValueError as e:
            logger.error('Discord configuration incorrect {}'.format(e))
            pass

    def get_config(self):
        return {'comm_port': self.discord_port,
                'server_address': self.discord_address,
                'cooldown': self.discord_cooldown,
                'enabled': self.discord_enabled,
                'on_demand': self.discord_on_demand,
                'triggering': self.discord_triggering
                }

    def discord_bot_comm(self):
        """
        Worker responsible for communicating with Discord bot.
        Sends whatever is in the internal queue
        :return: None
        """
        while self.discord_enabled:
            logger.debug('Waiting for message queue')
            msg = self.out_message_queue.get()
            logger.debug('Sending message to Discord bot, type: {}'.format(msg['type']))
            try:
                response = self.zmq_client.send_message(msg, 0, 1000)
            except Client.SendTimeout:
                logger.error('Cannot send message to Discord server')
                continue
            if response is None:
                logger.warning('Message response is None')
                continue
            logger.debug('Got response: {}'.format(response['type']))
            self.in_message_queue.put(response)

    def start_worker(self):
        self.discord_bot_comm_worker = threading.Thread(target=self.discord_bot_comm)
        self.discord_bot_comm_worker.setDaemon(True)
        logger.info('Starting bot thread')
        self.discord_bot_comm_worker.start()


class FeedPi:
    def __init__(self, config_file):
        self.config_file = config_file
        try:
            with open(self.config_file, 'r') as cnf_file:
                config = json.load(cnf_file)
        except FileNotFoundError:
            logging.error('Configuration file {} not found, quitting'.format(config_file))
            raise
        # defaults
        self.take_snaps = True
        self.take_videos = False
        self.images_dir = None
        self.videos_dir = None
        self.feed_res = [640, 480]
        self.loop_delay = 0.0
        self.overlay = True

        self.in_message_queue = queue.Queue()
        self.out_message_queue = queue.Queue()

        self.discord = Discord(config['discord'], self.in_message_queue, self.out_message_queue)
        self.apply_general_config(config['general'])
        self.vision = Vision(config['vision'])
        self.validate_dirs()

        self.movement_detected = self.vision.movement.is_triggered()
        self.last_scan = time.time()
        self.fps = 0.0
        self.movement_action_finished = True

        self.timer_worker = None
        self.message_thread = None
        self.start_workers()

    def send_image_to_discord(self):
        """
        Adds image message to discord queue
        :return: None
        """
        image_bytes = self.get_frame_jpg()
        msg = {"type": "send_image", "content": {"channel": None, "image_data": image_bytes,
                                                 "message": "Image caption", "file_name": "image.jpg"}}
        self.out_message_queue.put(msg)

    def evaluate_messages(self):
        """
        Evaluates message queues in a loop. It execution is blocked on taking message from incoming queue
        :return: None
        """
        while True:
            message = self.in_message_queue.get()
            if message['type'] == 'request_snap' and self.discord.discord_on_demand and self.discord.discord_enabled:
                logger.info('Discord requested an image.')
                self.send_image_to_discord()
            else:
                logger.debug('Nothing to do...')

    def timer(self):
        """
        Puts polling message that will request Discord Bot if there is a need to send image.
        This function has certain drift, but it does not matter in this application
        :return: None
        """
        while True:
            time.sleep(5)
            if self.discord.discord_enabled and self.discord.discord_on_demand:
                self.out_message_queue.put({"type": "request", "content": None})

    def start_workers(self):
        """
        Starts worker(s)
        :return: None
        """
        self.message_thread = threading.Thread(target=self.evaluate_messages)
        self.message_thread.setDaemon(True)
        logger.info('starting messages thread')
        self.message_thread.start()

        self.timer_worker = threading.Thread(target=self.timer)
        self.timer_worker.setDaemon(True)
        logger.info('starting timer thread')
        self.timer_worker.start()

    def apply_general_config(self, config_dict):
        try:
            self.loop_delay = float(config_dict['loop_delay'])
            self.overlay = config_dict['overlay']
            self.take_snaps = config_dict['save_images']
            self.images_dir = config_dict['images_dir']
            self.take_videos = config_dict['save_videos']
            self.videos_dir = config_dict['videos_dir']
            self.feed_res = [int(config_dict['feed_res'][0]), int(config_dict['feed_res'][1])]
        except KeyError as e:
            logger.error('General configuration file section is incorrect {}'.format(e))
            raise ConfigurationError

    def apply_discord_config(self, config_dict):
        self.discord.apply_config(config_dict)

    def change_config(self, config_dict):
        try:
            self.apply_general_config(config_dict['general'])
            self.apply_discord_config(config_dict['discord'])
        except ConfigurationError:
            return 'Invalid configuration'
        self.vision.apply_settings(config_dict['vision'])
        return 'OK'

    def save_settings(self):
        """
        Save settings to config file
        :return:  None
        """
        settings = self.get_settings()
        json.dump(settings, self.config_file)

    def get_settings(self):
        vision = self.vision.get_settings()
        discord = self.discord.get_config()
        return {'general': {'loop_delay': self.loop_delay,
                            'overlay': self.overlay,
                            'feed_res': self.feed_res,
                            'images_dir': self.images_dir,
                            'videos_dir': self.videos_dir,
                            'save_videos': self.take_videos,
                            'save_images': self.take_snaps},
                'vision': {**vision},
                'discord': {**discord}
                }

    @staticmethod
    def create_output_dirs(output_path, type_of_dir):
        """
        If output_path does not exist, create an output directory in script directory/data/type_of_dir
        :param output_path: Path of output files
        :param type_of_dir: Type of output dir
        :return: Correct path for file output
        """
        script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        if not os.path.isdir(output_path):
            logger.error('Error accessing {} directory {}'.format(type_of_dir, output_path))
            output_path = os.path.join(script_dir, 'data', type_of_dir)
            logger.warning('Changed {} directory to {}'.format(type_of_dir, output_path))
            try:
                os.makedirs(output_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    logger.warning('Cannot create {}, you may not be able to save {}'.format(output_path, type_of_dir))
                    raise
                pass
        return output_path

    def validate_dirs(self):
        """
        Valdiates output directoris
        :return: None
        """
        self.images_dir = self.create_output_dirs(self.images_dir, 'images')
        self.videos_dir = self.create_output_dirs(self.videos_dir, 'videos')

    def get_fps(self):
        """
        Calculates the frames per second number
        :return: returns FPS value
        """
        ts = time.time()
        try:
            fps = 1/(ts-self.last_scan)
        except ZeroDivisionError:
            fps = 0
        self.last_scan = ts
        return fps

    def loop(self):
        """
        Main task function. Runs once
        :return: None
        """
        self.fps = 0.2 * self.get_fps() + 0.8 * self.fps
        self.vision.refresh_feed()
        try:
            self.vision.get_image_diff()
            movement = self.vision.get_movement_level()
        except Exception as e:
            logger.error("Cant get movement level, setting to 0")
            movement = 0.0
        movement_detected, triggered = self.vision.movement.update_movement(movement)

        if triggered and not self.movement_action_finished:
            if self.take_snaps:
                self.save_image()
            if self.discord.discord_enabled and self.discord.discord_triggering:
                self.send_image_to_discord()
            self.movement_action_finished = True
        elif not triggered and self.movement_action_finished:
            self.movement_action_finished = False
        time.sleep(self.loop_delay)

    def save_image(self):
        self.vision.take_snap(self.images_dir)

    @staticmethod
    def calculate_movement(frame_threshold):
        return get_frame_mean(frame_threshold)

    def get_frame_jpg(self):
        """
        Converts numpy frame to jpg frame. Adds overlay if needed
        :return: jpg frame
        """
        img = resize_image(self.vision.frame, self.feed_res[0], self.feed_res[1])
        if self.overlay:
            y = len(img[0])
            text = "Movement: {:.3f} fps: {:.3}".format(self.vision.movement.curr_movement, self.fps)
            if self.vision.movement.triggered:
                color = (0, 100, 200)
            else:
                color = (0, 200, 0)
            cv2.putText(img, text, (int(y/50), int(y/25)), cv2.FONT_HERSHEY_SIMPLEX, y/700.0, color, int(y/250))
        return self.vision.convert_to_jpg(img)

    def get_frame_threshold_jpg(self):
        return self.vision.convert_to_jpg(self.vision.thresholded_frame)

    def get_mock_jpg(self):
        return self.vision.convert_to_jpg(get_jpg_from_frame(create_blank_image_b()))


class ConfigurationError(Exception):
    pass


def isip(ip):
    ip = str(ip)
    return re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) or ip.lower() == 'localhost'
