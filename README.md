rgstats
=======

Description
-----------

rgstats is a command line utility for the [Robot Game](http://robotgame.org/ "Robot Game").
The tool generates statistics based on numerous matches performed between any arbitrary number of robots.
Note that the underlying script is still the [rgkit](https://github.com/brandonhsiao/rgkit "rgkit") run.py but is multithreaded to be more efficient.
The results are either pretty printed in the shell itself or outputed as JSON.

Also, check them out:
- [rgsimulator](https://github.com/mpeterv/rgsimulator "rgsimulator")
- [rgcompare](https://github.com/mueslo/rgcompare "rgcompare")

Installation
---------------

The prerequisits are exactly the same as the [rgkit](https://github.com/brandonhsiao/rgkit "rgkit") itself.

Commands:

	cd /path/to/destination
	git clone https://github.com/throskam/rgstats.git
	cd rgstats
	chmod +x rgstats.py
	git clone https://github.com/brandonhsiao/rgkit.git
	mkdir bots
	cd bots
	git clone https://github.com/mpeterv/robotgame-bots.git

You can now place your bots in the _bots_ directory.
Time to time you get run `git pull` in the different git repositories in order to keep them up to date.

Usage
-----

	usage: rgstats.py [-h] [-d DIR [DIR ...]] [-c COUNT] [-t THREADS] (-v | -f) (-j | -l) robot [opponent [opponent ...]]

	positional arguments:
	  robot                                 robot name
	  opponent                              opponents robot name

	optional arguments:
	  -h, --help                            show this help message and exit
	  -d DIR [DIR ...], --dir DIR [DIR ...] import robots from directory
	  -c COUNT, --count COUNT               game count, [1]
	  -t THREADS, --threads THREADS         amount of parallel threads (use with caution !) [#processors]
	  -v, --vip                             me against the world
	  -f, --free                            free for all
	  -j, --json                            print JSON format
	  -l, --cli                             pretty print result in the console

Example
-------

	./rgstats YOUR_BOT SECOND_BOT THIRD_BOT -d DIR_BOT SECOND_DIR_BOT -fl -c 10 -t 8