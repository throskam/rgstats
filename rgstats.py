#!/usr/bin/python
# -*- coding: utf-8 -*-
from multiprocessing.dummy import Pool
import multiprocessing
import subprocess
import argparse
import json
import sys
import warnings
import string
import os

version = '0.1'

# Remove warnings ...
warnings.filterwarnings('ignore', message='BaseException.message has been deprecated as of Python 2.6', category=DeprecationWarning, module='argparse')

parser = argparse.ArgumentParser(description='Game Robots statistics tool');

parser.add_argument('robot', help='robot name')
parser.add_argument('opponent', help='opponents robot name', nargs='*')
parser.add_argument('-d', '--dir', help='import robots from directory', nargs='+')
parser.add_argument('-c', '--count', help='game count, [1]', type=int, default=1)
parser.add_argument('-t', '--threads', help='amount of parallel threads (use with caution !) [#processors]', type=int, default=multiprocessing.cpu_count())

mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('-v', '--vip', help='me against the world', action='store_true')
mode.add_argument('-f', '--free', help='free for all', action='store_true')

interface = parser.add_mutually_exclusive_group(required=True)
interface.add_argument('-j', '--json', help='print JSON format', action='store_true')
interface.add_argument('-l', '--cli', help='pretty print result in the console', action='store_true')

args = parser.parse_args()

# Retrieve the name from a script path
def name(path):
	return os.path.splitext(os.path.basename(path))[0]

# Perform a match between the given 2 robots and return the scores or an error
def perform(robots):
	process = subprocess.Popen(['python', './rgkit/run.py', '-H', robots[0], robots[1]], stdout=subprocess.PIPE)
	out, err = process.communicate()
	score = out.rstrip().replace('[', '').replace(']', '').replace(',', '').split(' ')

	if err is not None or len(score) != 2:
		return {
			'status': process.returncode,
			'error': err,
			'robots': (name(robots[0]), name(robots[1]))
		}

	result = {}

	result[name(robots[0])] = int(score[0])
	result[name(robots[1])] = int(score[1])

	return result

# Perform the match between two robots the required number of times and collects the associated outputs
def match(bot, opponent):
	# List of match's results
	results = []

	# List of matches to perform
	matches = [[bot, opponent]] * args.count

	# Threads the matches and collect results
	pool = Pool(args.threads)
	for match in pool.imap_unordered(perform, matches):
		results.append(match)

	return stat_create(results)

def stat_robot():
	return {
		'info': {
			'match': 0,
			'success': 0,
			'failure': 0,
		},
		'matches': {},
	}

def stat_match(stats, match):
	if 'error' in match:
		bot, opp = match['robots']
	else:
		bot, opp = list(match)

	stats_gl = stats
	stat_bot = stats.get('robots').get(bot, stat_robot())
	stat_opp = stats.get('robots').get(opp, stat_robot())

	stats_gl['info']['match'] += 1
	stat_bot['info']['match'] += 1
	stat_opp['info']['match'] += 1

	if 'error' in match:
		stats_gl['info']['errors'].append((match['status'], match['error']))
		stats_gl['info']['failure'] += 1
		stat_bot['info']['failure'] += 1
		stat_opp['info']['failure'] += 1

	else:
		stats_gl['info']['success'] += 1
		stat_bot['info']['success'] += 1
		stat_opp['info']['success'] += 1


		if not opp in stat_bot['matches']:
			stat_bot['matches'][opp] = []

		if not bot in stat_opp['matches']:
			stat_opp['matches'][bot] = []

		stat_bot['matches'][opp].append(match)
		stat_opp['matches'][bot].append(match)

	stats_gl['robots'][bot] = stat_bot
	stats_gl['robots'][opp] = stat_opp

	return stats_gl

def stat_create(matches=None):
	stats =  {
		'info': {
			'match': 0,
			'success': 0,
			'failure': 0,
			'errors': []
		},
		'robots': {}
	}

	if matches is None:
		return stats

	for match in matches:
		stats = stat_match(stats, match)

	return stats

def stat_extend(stats, patch):
	stats['info']['match'] += patch['info']['match']
	stats['info']['success'] += patch['info']['success']
	stats['info']['failure'] += patch['info']['failure']

	for bot, stat in patch['robots'].items():
		# No stats for the bot
		if not bot in stats['robots']:
			stats['robots'][bot] = stat
			continue
		# Update stats
		stats['robots'][bot]['info']['match'] += stat['info']['match']
		stats['robots'][bot]['info']['success'] += stat['info']['success']
		stats['robots'][bot]['info']['failure'] += stat['info']['failure']

		for opp, matches in stat['matches'].items():
			# No matches for the opponent
			if not opp in stats['robots'][bot]['matches']:
				stats['robots'][bot]['matches'][opp] = matches
				continue

			# Update the matches
			stats['robots'][bot]['matches'][opp].extend(stat['matches'][opp])

	return stats

def stat_opp(bot, opp, matches):
	stats = {
		'win': 0,
		'lose': 0,
		'draw': 0
	}

	for match in matches:
		if match[bot] > match[opp]:
			stats['win'] += 1
		elif match[bot] < match[opp]:
			stats['lose'] += 1
		else:
			stats['draw'] += 1

	return stats

def stat_computed(stats):
	for bot, stat in stats['robots'].items():
		computed = {}
		for opp, matches in stat['matches'].items():
			computed[opp] = stat_opp(bot, opp, matches)
		stat['computed'] = computed
		stats['robots'][bot] = stat
	return stats

def turn(bot, robots):
	stats = stat_create()
	for opponent in robots:
		if bot == opponent:
			continue
		stats = stat_extend(stats, match(bot, opponent))
	return stats

def tourney(robots):
	stats = stat_create()
	for bot in robots:
		stats = stat_extend(stats, turn(bot, robots))
	return stats

###############################################################################
#                                 M A I N                                     #
###############################################################################

if __name__ == '__main__':
	opponents = args.opponent[:]

	if args.dir is not None:
		for d in args.dir:
			for filename in os.listdir(d):
				if '.py' in filename:
					opponents.append(d + ('' if d[-1] == '/' else '/') + filename)

	opponents = list(set(opponents))

	if args.vip:
		mode = 'vip'
		results = turn(args.robot, opponents)
	elif args.free:
		mode = 'free for all'
		opponents.append(args.robot)
		results = tourney(opponents)

	results = stat_computed(results)

	if args.json:
		print json.dumps(results)
	else:
		print '|' + '—' * 50 + '|'
		print '|' + ' ' * 50 + '|'
		print '|' + string.center('=> ' + sys.argv[0] + ' -v ' + version + ' <=', 50, ' ') + '|'
		print '|' + ' ' * 50 + '|'
		print '|' + '—' * 50 + '|'
		print '|' + string.center('C O N F I G U R A T I O N', 50, ' ') + '|'
		print '|' + '—' * 50 + '|'
		print '|%24s: %-24s|' % ('Robot', args.robot)
		for opp in args.opponent:
			print '|%24s: %-24s|' % ('Opponent', opp)
		print '|%24s: %-24s|' % ('Mode', mode)
		print '|%24s: %-24d|' % ('Count', args.count)
		print '|%24s: %-24d|' % ('Threads', args.threads)
		print '|' + '—' * 50 + '|'
		print '|' + string.center('R E S U L T S', 50, ' ') + '|'
		print '|' + '—' * 50 + '|'
		print '|' + ' ' * 50 + '|'
		print '|' + string.ljust(' '*5 + 'Global informations', 50, ' ') + '|'
		print '|' + string.center('='*40, 50, ' ') + '|'
		print '|' + ' ' * 50 + '|'
		print '|%24s: %-24d|' % ('Total', results['info']['match'])
		print '|%24s: %-24d|' % ('Success', results['info']['success'])
		print '|%24s: %-24d|' % ('Failure', results['info']['failure'])
		print '|' + ' ' * 50 + '|'
		print '|' + string.ljust(' '*5 + 'Robots', 50, ' ') + '|'
		print '|' + string.center('='*40, 50, ' ') + '|'
		print '|' + ' ' * 50 + '|'

		for bot, stat_bot in results['robots'].items():
			print '|' + string.center(bot, 50, ' ') + '|'
			print '|' + string.center('-'*30, 50, ' ') + '|'
			print '|%24s: %-24d|' % ('Total', stat_bot['info']['match'])
			print '|%24s: %-24d|' % ('Success', stat_bot['info']['success'])
			print '|%24s: %-24d|' % ('Failure', stat_bot['info']['failure'])
			print '|' + ' ' * 50 + '|'
			for opp, stat_opp in results['robots'][bot]['computed'].items():

				print '|          %-12s vs. %13s          |' % ('[' + str(stat_opp['win']) + ', ' + str(stat_opp['draw']) + ', ' + str(stat_opp['lose']) + ']', (opp[:11] + '..') if len(opp) > 13 else opp)
			print '|' + ' ' * 50 + '|'
		print '|' + '—' * 50 + '|'