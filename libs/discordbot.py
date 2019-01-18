import logging
from discord.ext import commands
from discord import errors

import queue
import threading
import asyncio
import io
import json

from .zmqconnector.connector import Server as zeromqServer
logger = logging.getLogger(__name__)


class FpiBot(commands.Bot):
    def __init__(self, config_file):
        with open(config_file, 'r') as conf_file:
            config = json.load(conf_file)
        super().__init__(command_prefix=config['discord_config']['command_prefix'],
                         description=config['discord_config']['description'])
        self.token = config['discord_config']['token']
        self.server = zeromqServer(config['discord_config']['connector_port'])
        self.spi_channel_id = config['discord_config']['bot_channel']
        self.general_channel_id = config['discord_config']['general_channel']
        self.q_inbound = queue.Queue()
        self.q_outbound = queue.Queue()
        self.request_snap = False
        self.loop.create_task(self.background_task_q_evaluate())
        self.worker_thread = None

    def start_bot(self):
        self.start_worker()
        self.run(self.token)

    def worker(self):
        while True:
            logger.debug('Waiting for message from socket')
            msg = self.server.receive_message(blocking=True)
            logger.debug('Got message')
            response = self.evaluate_incoming_request(msg)
            logger.debug('Prepared response: {}'.format(response))
            self.server.send_message(response)

    def evaluate_incoming_request(self, msg):
        """

        :param msg:
        :return:
        """
        response = {'type': 'response',
                    'content': None}
        if msg['type'] == 'send_image' or msg['type'] == 'send_message':
            self.q_inbound.put(msg)
        if msg['type'] == 'request':
            try:
                response = self.q_outbound.get(False)
            except queue.Empty:
                logger.debug('returning response: {}'.format(response))
                return response
        return response

    def start_worker(self):
        self.worker_thread = threading.Thread(target=self.worker)
        self.worker_thread.setDaemon(True)
        logger.info('starting thread')
        self.worker_thread.start()
        logger.info('started')

    @staticmethod
    async def on_ready():
        """
        Function triggered on successful bot login
        """
        logger.info('Logged in')

    async def send_image(self, image_data, image_name=None, channel=None, message=None):
        """
        Send image to channel
        :param image_data: image bytes
        :param image_name: image filename
        :param channel: send channel
        :param message: optional caption of the image
        :return:
        """
        logger.debug('Sending image')
        if channel is None:
            channel = self.spi_channel_id
        if image_name is None:
            image_name = 'image.png'
        stream = io.BufferedReader(io.BytesIO(image_data))
        await self.send_file(self.get_channel(channel), stream, filename=image_name, content=message)

    async def send_text_message(self, message, channel=None):
        """
        Sends text message to channel
        :param message: Message to send
        :param channel: Message channel
        :return:
        """
        logger.debug('sending massage')
        if channel is None:
            channel = self.spi_channel_id
        await self.send_message(self.get_channel(channel), message)

    async def background_task_q_evaluate(self):
        """
        Background task that is monitoring incoming queue
        :return: None
        """
        logger.info('starting background task')
        await self.wait_until_ready()
        while not self.is_closed:
            await asyncio.sleep(1)  # task runs every 60 seconds
            try:
                msg = self.q_inbound.get(False)
                logger.debug('New message received from queue! Type {}'.format(msg['type']))
            except queue.Empty:
                continue
            await self.evaluate_inbound(msg)

    async def evaluate_inbound(self, msg):
        """
        Evaluates inbound message and run appropiate function
        :param msg: dictionary messsage to evaluate
        :return: None
        """
        if msg['type'] == 'send_image':
            logger.debug('Evaluated send image')
            await self.send_image(msg['content']['image_data'],
                                  image_name=msg['content']['file_name'],
                                  channel=msg['content']['channel'],
                                  message=msg['content']['message'])
        if msg['type'] == 'send_message':
            await self.send_text_message(msg['content']['message'],
                                         channel=msg['content']['channel'])


def create_bot(config):
    """
    This look terrible, but I failed define bot commands inside a class. Probably something easy...
    :param config: config file
    :return: configured bot
    """

    bot = FpiBot(config)

    @bot.command(pass_context=True)
    async def spi_snap(ctx):
        """
        Puts request to send latest frame into outgoing queue
        :param ctx: context
        :return: None
        """
        bot.q_outbound.put({'type': 'request_snap',
                            'content': {'channel_id': ctx.message.channel}})

    @bot.command(pass_context=True)
    async def clear(ctx, number=2):
        """
        Clears messages from the channel that this command was send from
        :param ctx: context
        :param number: number of messages to delete
        :return: None
        """
        logger.info("Clearing {} last messages".format(number))
        msgs = []
        number = int(number)
        async for x in bot.logs_from(ctx.message.channel, limit=number):
            msgs.append(x)
        try:
            await bot.delete_messages(msgs)
        except errors.HTTPException as e:
            if e.code == 50034:
                logger.warning('Trying to delete messages older than 14 days, changing to single mode')
                for msg in msgs:
                    await bot.delete_message(msg)
            else:
                raise e
        except errors.ClientException:
            logger.warning('Clear command for messages that are not on server')
    return bot


if __name__ == '__main__':
    pass
