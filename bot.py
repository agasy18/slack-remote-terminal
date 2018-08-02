import time
import re
from slackclient import SlackClient
import json
import inspect
import os
import traceback
import threading
import tempfile
import subprocess

with open('config.json') as f:
    config = json.load(f)

SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN'] or config['SLACK_BOT_TOKEN']

# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)

# constants
RTM_READ_DELAY = 0.5  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
MENTION_REGEX_EMPTY = ".*<@(|[WU].+?)>.*"


def ignore_exception(ignore_exception=Exception, default_val=None):
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except ignore_exception:
                return default_val

        return _dec

    return dec


class Commands:
    @staticmethod
    def help(args, reply, api_call, event):
        """
        list all commands and print help
        """
        reply('\n'.join(["`{}`\n{}".format(name, m.__doc__)
                         for name, m in inspect.getmembers(Commands, predicate=inspect.isfunction)]),
              thread_ts=event['ts'], reply_broadcast=True)

    @staticmethod
    def upload(args, reply, api_call, event):
        """
        get file from host
        _ upload file_path _
        """
        if not args:
            reply('you mast send me file path', 'upload error', reply_broadcast=True)

        path = os.path.expanduser(' '.join(args))
        if os.path.isdir(path):
            reply('`{}` is a directory, this is not supported yet'.format(path), 'upload error', reply_broadcast=True)
        elif os.path.isfile(path):
            reply('Uploading', thread_ts=event['ts'])
            with open(path, 'rb') as f:
                api_call('files.upload',
                         file=f,
                         filename=os.path.basename(path),
                         filetype=os.path.splitext(path)[-1],
                         title=path, reply_broadcast=True)
        else:
            reply('`{}` file not found'.format(path), 'upload error', reply_broadcast=True)

    log_files = {}

    @staticmethod
    def terminal(args, reply, api_call, event):
        """
        execute command/script on bash or other interpreter
        _ command/script _
        or
        _ terminal command/script _
        """

        f = tempfile.NamedTemporaryFile()
        proc = subprocess.Popen(config["INTERPRETER"],
                                stderr=f.file,
                                stdout=f.file,
                                stdin=subprocess.PIPE,
                                cwd=os.path.expanduser('~'))

        Commands.log_files[str(proc.pid)] = f
        command = ' '.join(args)
        reply('Runing on {}'.format(proc.pid))
        proc.communicate(command.encode())
        fl = f.tell()
        f.seek(0)
        if fl < config['MAX_TEXT_SIZE']:
            reply(f.read(), mrkdwn=False, reply_broadcast=True)
        else:
            api_call('files.upload',
                     file=f,
                     filename='log.txt',
                     filetype='txt',
                     title=command,
                     reply_broadcast=True)

        f.close()
        del Commands.log_files[str(proc.pid)]
        title = '{} exited with: {}'.format(proc.pid, proc.returncode)
        reply(title, reply_broadcast=fl >= config['MAX_TEXT_SIZE'])

    @staticmethod
    def getlog(args, reply, api_call, event):
        """
        get log from active process which was scheduled by bot
        _ getlog process_id [size] _
        """

        if not args:
            reply("Process id not passed", "Error", reply_broadcast=True)

        args = [a.strip() for a in args]
        pid = args[0]
        if pid in Commands.log_files:
            log_file = Commands.log_files[pid]
            fl = log_file.file.tell()
            with open(log_file.name, 'rb') as f:
                if len(args) > 1:
                    nl = args[1]
                    try_pars_int = ignore_exception(ValueError)(int)
                    v = try_pars_int(nl)
                    if not v:
                        reply("`{}` is not int".format(nl), "Error", reply_broadcast=True)
                        return
                    v = min(v, fl)
                    f.seek(-v, 2)
                    fl = v

                if fl < config['MAX_TEXT_SIZE']:
                    reply(f.read(), mrkdwn=False, reply_broadcast=True)
                else:
                    api_call('files.upload',
                             file=f,
                             filename='log.txt',
                             filetype='txt',
                             title=str(pid),
                             reply_broadcast=True)
        else:
            reply('can\'t find process id {}', "Error", reply_broadcast=True)


def parse_bot_commands(slack_events, bot_id, ims):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"], event, ims, bot_id)
            if user_id == bot_id:
                # remove url tags
                match = re.match('(.*)<(.+?)\|(.+?)>(.*)', message)
                if match:
                    message = match.group(1) + match.group(3) + match.group(4)
                return message, event
    return None, None


def parse_direct_mention(message_text, event, ims, bot_id):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention or direct message, returns None
    """

    print ("Processing: " + message_text)

    matches = re.search(MENTION_REGEX, message_text)
    if matches:
        return matches.group(1), matches.group(2).strip()
    matches = re.search(MENTION_REGEX_EMPTY, message_text)
    if matches:
        return matches.group(1), ''
    if event['channel'] in ims:
        return bot_id, message_text

    return None, None


def handle_command(command, event):
    """
        Executes bot or terminal command
    """
    start_time = time.time()
    channel = event['channel']

    def api_call(*args, **kwargs):
        if time.time() - start_time > config['MENTION_CHANNEL_AFTER']:
            if time.time() - start_time:
                kwargs['text'] = '<!channel> \n' + (kwargs['text'] if 'text' in kwargs else '')

        if 'files.upload' in args:
            kwargs['channels'] = channel
        elif 'chat.postMessage' in args:
            kwargs['channel'] = channel
        kwargs['thread_ts'] = event['ts']

        j = slack_client.api_call(*args, **kwargs)
        if 'ok' not in j or not j['ok']:
            print('Method: {}\n, args:{}\n response: {}'.format(args, kwargs, json.dumps(j, indent=2)))
        return j

    def reply(text, title=None, **kwargs):
        if title:
            text = '*{}*\n{}'.format(title, text)
        if not text:
            text = '`Empty`'
        return api_call("chat.postMessage", text=text, **kwargs)

    if not command:
        Commands.help([], reply, api_call, event)
        return

    subs = command.split(' ')
    if hasattr(Commands, subs[0]):
        ex = getattr(Commands, subs[0])
        subs = subs[1:]
    else:
        ex = Commands.terminal

    def runInThread():
        try:
            ex(subs, reply, api_call, event)
        except:
            reply("```\n{}\n```".format(traceback.format_exc()), 'Error')

    thread = threading.Thread(target=runInThread)
    thread.start()


def run_loop():
    if slack_client.rtm_connect(with_team_state=False):
        print("Terminal Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        test = slack_client.api_call("auth.test")
        bot_id = test["user_id"]
        ims_r = slack_client.api_call("im.list", limit=1000)
        if 'ok' not in ims_r or not ims_r['ok'] or 'ims' not in ims_r:
            print("Can't get direct messages list : ".format(json.dumps(ims_r)))
            return
        ims = [x['id'] for x in ims_r['ims']]
        print('User info:')
        print(json.dumps(test))
        for im in ims:
            slack_client.api_call('chat.postMessage',
                                  channel=im,
                                  text='Hello I am {}, ready to help you'.format(test['user']))
        while True:
            command, event = parse_bot_commands(slack_client.rtm_read(), bot_id, ims)
            if command is not None:
                handle_command(command, event)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")


if __name__ == "__main__":
    while True:
        try:
            run_loop()
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except:
            traceback.print_exc()
            time.sleep(10)
            pass
