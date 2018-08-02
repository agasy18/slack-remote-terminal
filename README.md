# Slack Remote Terminal
Control remote host via Slack

## Run tasks on remote host via Slack
Run tasks via slack by mentioning bot at binging of quarry from channels
```
@host_bot uptime
```
Or write direct message to bot
```
uptime
```

bot will reply in the thread

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

Bot will run `uptime` command on bash and will reply you with output. If output is large (see in `config.json` and slack message length restrictions) than bot will send you the log as file

## Alerting and long tasks
Run long task (neuaral network training, big computaion, file copying, scanning, etc.) and get alert from bot about the task compleation *status* and *log*.

for example lets
```
ping googe.com
```
bot will reply you
```
Runing on 3677
```

as this task is infinite, it will never stop itself
To get log at any time for not completed tasks use `getlog` command

```
getlog 3677
```

bot reply

```
PING googe.com (162.243.10.151) 56(84) bytes of data.
64 bytes from 162.243.10.151: icmp_seq=1 ttl=50 time=151 ms
64 bytes from 162.243.10.151: icmp_seq=2 ttl=50 time=151 ms
64 bytes from 162.243.10.151: icmp_seq=3 ttl=50 time=151 ms
```

to get last 1000 bytes from log pass it to `getlog`
```
getlog 3677 1000
```
if you task was stppoed or killed (`@host_bot bash kill -9 3677`) bot will alert by metioning *@channel*
```
@host_bot replied to a thread: @host_bot ping googe.com (attached log file)
@channel
3677 exited with: -9
```

## Uplading files from host to Slack
```
upload file_path
```

## Instalation
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
python boy.py
#or
python3 boy.py
```

Note: if some error was accured bot will log an error and try reconnect
