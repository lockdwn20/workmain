# The show-ids option is not working for workmain time command

```
(.venv) lockdwn20@ana:~/Projects/workmain$ workmain time --show-ids
Usage: workmain time [OPTIONS] COMMAND [ARGS]...
Try 'workmain time --help' for help.

Error: No such option: --show-ids
```

# The meeting condensed summary appears to be summarizing all notes even the ones mark #ifo

unable to push time track entries:
(.venv) lockdwn20@ana:~/Projects/workmain$ workmain track sync push
Traceback (most recent call last):
  File "/home/lockdwn20/Projects/workmain/.venv/bin/workmain", line 7, in <module>
    sys.exit(cli())
             ^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1157, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1078, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1434, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 783, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/workmain/cli/commands/track.py", line 428, in push
    session = get_session()
              ^^^^^^^^^^^
NameError: name 'get_session' is not defined


# When I added a note and sync to clockify it showed up as the wrong time and date in clockify and do not show up in today's notes even though all notes should default to today:

(.venv) lockdwn20@ana:~/Projects/workmain$ workmain track add " Completed the Google PMLE Tensorflow API lab.  Went over importing and analyzing a dataset using the Tensorflow API" 1.5h --time 0530
✓ Time entry added (ID: 2)
  1.5h -  Completed the Google PMLE Tensorflow API lab.  Went over importing and analyzing a dataset using the Tensorflow API
  Time: 05:30

Sync to Clockify now? [y/N]: y
[1/1] Syncing:  Completed the Google PMLE Tensorflow API lab.  We...
  ✓ Synced (Clockify ID: 6980c893...)
✓ Synced to Clockify

From the Clockify Website:
Yesterday
Completed the Google PMLE Tensorflow API lab.  Went over importing and analyzing a dataset using the Tensorflow API
assets/ui-icons/plus-blue.svg
Project
Tag empty
21:30
23:00
01:30:00

# Trying to review the previous days notes to find the one I inputted for today that showed up in clockify for yesterday and I received the following error:
(.venv) lockdwn20@ana:~/Projects/workmain$ workmain notes date yesterday
Traceback (most recent call last):
  File "/home/lockdwn20/Projects/workmain/.venv/bin/workmain", line 7, in <module>
    sys.exit(cli())
             ^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1157, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1078, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1688, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 1434, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/.venv/lib/python3.12/site-packages/click/core.py", line 783, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/lockdwn20/Projects/workmain/workmain/cli/commands/note.py", line 698, in date
    query_date = date.today() - timedelta(days=1)
                 ^^^^^^^^^^
AttributeError: 'Command' object has no attribute 'today'


# It appears that if you use the workmain track command it does not save the time tracking command in the notes.  If it is saved in the database then it needs to be fixed to create a note because there is no way to view the track entries.

# There is a definite disconnect between meeting/meetings, not/notes, and track, they don't seem to be referencing the corrrect information stored in the database.  Unable to see all the notes