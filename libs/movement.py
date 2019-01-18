import time
from numpy import mean
import logging

logger = logging.getLogger('movement')


class Movement:
    def __init__(self, config):
        # Defaults
        self.movement_threshold = 15
        self.low_pass = False
        self.take_snaps = False
        self.movement_cooldown = 10.0

        self.apply_settings(config)

        self.curr_movement = 0.0

        self.last_trigger = time.time()
        self.triggered = True

    def apply_settings(self, config):
        self.movement_cooldown = int(config['movement_cooldown'])
        self.movement_threshold = config['movement_threshold']
        self.low_pass = config['movement_low_pass']

    def get_settings(self):
        return {'movement_cooldown': self.movement_cooldown,
                'movement_threshold': self.movement_threshold,
                'movement_low_pass': self.low_pass}

    def update_movement(self, movement):
        """
        Updates movement level. It does not take into consideration elapsed time since last update
        :param movement: New movement level
        :return: tuple fo movement detection and trigger state
        """
        if self.low_pass:
            self.curr_movement = 0.7*self.curr_movement + 0.3*movement
        else:
            self.curr_movement = movement
        logger.debug('Registred movement with level {}'.format(self.curr_movement))
        movement_detected = self.is_movement_detected()
        triggered = self.is_triggered()
        return movement_detected, triggered

    def is_movement_detected(self):
        """
        Checks if current movement is over the thereshold
        :return: detection result
        """
        if self.curr_movement > self.movement_threshold:
            logger.debug('Movement detected!')
            return True
        return False

    def is_triggered(self):
        """
        Checks if movement is in triggered state, that is if it is past the cooldown period since last detection
        :return: trigger result
        """
        ts = time.time()
        movement = self.is_movement_detected()
        if movement and not self.triggered and ts-self.last_trigger > self.movement_cooldown:
            logger.debug('Setting trigger')
            self.triggered = True
            self.last_trigger = ts
        elif self.triggered and ts-self.last_trigger > self.movement_cooldown:
            logger.debug('Resetting trigger')
            self.triggered = False
        return self.triggered

    @staticmethod
    def get_movement_level(frame):
        """
        Calculates the movement level- white pixels in the frame
        :param frame: frame array
        :return: calculated movement level
        """
        return mean(frame)
