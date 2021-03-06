from __future__ import unicode_literals
import json
import urllib2
import codecs
import sys


utf8_stdout = codecs.getwriter('utf8')(sys.stdout)

def get_data(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except IOError:
        return []

def init():
    hammy = set(get_data('hammy.json'))
    spammy = set(get_data('spammy.json'))
    return hammy, spammy

def get_feed():
    fd = urllib2.urlopen(
        'http://forum.openhatch.org/discussions.json')
    s = fd.read()
    return json.loads(s)

def prompt_for_spammy_content(spam_author_ids,
                              iterable_of_discussions, spammy, hammy,
                              max_prompts=None, no_input=False):
    prompts_so_far = 0

    for discussion in iterable_of_discussions:
        author_id = int(discussion['FirstUserID'])
        if author_id in spam_author_ids:
            continue # next discussion
        if author_id in spammy:
            continue # next discussion
        if author_id in hammy:
            continue # next discussion

        prompts_so_far += 1
        if (max_prompts is not None) and (prompts_so_far > max_prompts):
            return

        body = discussion['Body']
        print >> utf8_stdout, body

        print >> utf8_stdout, "Is this spam?"
        yes_no = raw_input("y/N >")[:1].lower()
        if yes_no == 'y':
            spam_author_ids.add(author_id)
        else:
            hammy.add(author_id)

def in_feed_look_for_spammy_users(feed, hammy, spammy, max_prompts=None, no_input=False):
    spam_authors = set()
     
    if hasattr(feed['Discussions'], 'values'):
        discussions = feed['Discussions'].values()
    else:
        discussions = feed['Discussions']

    discussions_reformatted = [
        value for value in discussions
        if value]

    for data_source in (
        feed['Announcements'],
        discussions_reformatted):
        prompt_for_spammy_content(spam_authors,
                                  data_source,
                                  spammy,
                                  hammy,
                                  max_prompts,
                                  no_input)

    return hammy, spam_authors

def make_deletion_urls(user_ids):
    for user_id in user_ids:
        print >> utf8_stdout, "You should go delete these discussions:"
        print >> utf8_stdout, "http://forum.openhatch.org/profile/discussions/%d/contrib" % (
            user_id,)
        print >> utf8_stdout, "and then go mark the user as Banned by visiting their profile and editing them:"
        print >> utf8_stdout, "http://forum.openhatch.org/user/edit/%d" % (
            user_id,)
        print >> utf8_stdout, ""

def save(hammy, spammy):
    with open('hammy.json', 'w') as fd:
        json.dump(sorted(hammy), fd)

    with open('spammy.json', 'w') as fd:
        json.dump(sorted(spammy), fd)

def main(no_input=False):
    hammy, spammy = init()
    feed = get_feed()
    hammy, new_spammy = in_feed_look_for_spammy_users(feed, hammy, spammy, max_prompts=5, no_input=no_input)
    make_deletion_urls(new_spammy)
    spammy.update(new_spammy)
    save(hammy, spammy)

if __name__ == '__main__':
    import sys
    if '--no-input' in sys.argv:
        no_input=True
    else:
        no_input=False
    main(no_input)
