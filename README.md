# Slack Remote Terminal
Control remote host via Slack

## Run tasks on remote host via Slack
Run tasks via slack by mentioning bot at binging of a query from channels
```
@host_bot uptime
```
Or write a direct message to the bot
```
uptime
```

the bot will reply in the thread

_process id_
```
Runing on 3526
```
_output_
```
16:12:44 up 23 min,  1 user,  load average: 1.18, 1.06, 0.75
```
_exit code_
```
3526 exited with: 0
```

The bot will run `uptime` command on bash and will reply to you with output. If the output is large (see in `config.json` and slack message length restrictions) then the bot will send you the log as a file.

## Alerting and long tasks
Run long tasks (neural network training, big computation, file copying, scanning, etc.) and get alert from bot about the task completion *status* and *log*.

For example on
```
ping googe.com
```
bot will reply
```
Runing on 3677
```

as this task is infinite, it will never stop itself
To get a log at any time for not completed tasks use `getlog` command

```
getlog 3677
```

bot will reply

```
PING googe.com (162.243.10.151) 56(84) bytes of data.
64 bytes from 162.243.10.151: icmp_seq=1 ttl=50 time=151 ms
64 bytes from 162.243.10.151: icmp_seq=2 ttl=50 time=151 ms
64 bytes from 162.243.10.151: icmp_seq=3 ttl=50 time=151 ms
```

to get last 1000 bytes from pass it at the end of `getlog` command
```
getlog 3677 1000
```
if your task was stppoed or killed (`@host_bot bash kill -9 3677`) the bot will alert it by metioning *@channel*
```
@host_bot replied to a thread: @host_bot ping googe.com (attached log file)
@channel
3677 exited with: -9
```

## Uplading files from host to Slack
```
upload file_path
```

## Installation
Download the code or clone
```
git clone https://github.com/agasy18/slack-remote-terminal.git
```

##### Install the Slack API
```
pip install slackclient
```

##### Setting `SLACK_BOT_TOKEN`
Create a new [Slack bot](https://api.slack.com/apps/new) (see [tutorial](https://www.fullstackpython.com/blog/build-first-slack-bot-python.html))

change `SLACK_BOT_TOKEN` in `config.json` file or just export it
```
export SLACK_BOT_TOKEN='your bot user access token here'
```

##### Run the bot
```bash
cd slack-remote-terminal
python3 -m pip install slackclient
python3 boy.py
```

Note: if some error was accured bot will log an error and try reconnect
