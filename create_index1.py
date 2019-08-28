#!/usr/bin/env python

"""Parse the enwiki-latest-pages-meta-history.xml file."""

from __future__ import with_statement

import os
import io
from contextlib import closing
# from StringIO import StringIO
from optparse import OptionParser
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# from blueplate.parsing.tsv import create_default_writer

__docformat__ = "restructuredtext"


class WPXMLHandler(ContentHandler):

    """Parse the enwiki-latest-pages-meta-history.xml file.

    This parser looks for just the things we're interested in.  It maintains a
    tag stack because the XML format actually does have some depth and context
    does actually matter.

    """

    def __init__(self, page_handler):
        """Do some setup.

        page_handler
            This is a callback.  It will be a called with a page in the form
            of a dict such as::

                {'id': u'8',
                 'revisions': [{'timestamp': u'2001-01-20T15:01:12Z',
                                'user': u'ip:pD950754B.dip.t-dialin.net'},
                               {'timestamp': u'2002-02-25T15:43:11Z',
                                'user': u'ip:Conversion script'},
                               {'timestamp': u'2006-09-08T04:16:46Z',
                                'user': u'username:Rory096'},
                               {'timestamp': u'2007-05-24T14:41:48Z',
                                'user': u'username:Ngaiklin'},
                               {'timestamp': u'2007-05-25T17:12:09Z',
                                'user': u'username:Gurch'}],
                 'title': u'AppliedEthics'}

        """
        self._tag_stack = []
        self._page_handler = page_handler

    def _try_calling(self, method_name, *args):
        """Try calling the method with the given method_name.

        If it doesn't exist, just return.

        Note, I don't want to accept **kargs because:

         a) I don't need them yet.
         b) They're really expensive, and this function is going to get called
            a lot.

        Let's not think of it as permature optimization, let's think of it as
        avoiding premature flexibility ;)

        """
        try:
            f = getattr(self, method_name)
        except AttributeError:
            pass
        else:
            return f(*args)

    def startElement(self, name, attr):
        """Dispatch to methods like _start_tagname."""
        self._tag_stack.append(name)
        self._try_calling('_start_' + name, attr)
        self._setup_characters()

    def _start_page(self, attr):
        self._page = dict(revisions=[])

    def _start_revision(self, attr):
        self._page['revisions'].append({})

    def endElement(self, name):
        """Dispatch to methods like _end_tagname."""
        self._teardown_characters()
        self._try_calling('_end_' + name)
        self._tag_stack.pop()

    def _end_page(self):
        self._page_handler(self._page)

    def _setup_characters(self):
        """Setup the callbacks to receive character data.

 The Parser will call the "characters" method to report each chunk of
 character data.  SAX parsers may return all contiguous character data
 in a single chunk, or they may split it into several chunks.  Hence,
 this class has to take care of some buffering.

        """
        method_name = '_characters_' + '_'.join(self._tag_stack)
        if hasattr(self, method_name):
            self._characters_buf = io.StringIO()
        else:
            self._characters_buf = None

    def characters(self, s):
        """Buffer the given characters."""
        if self._characters_buf is not None:
            self._characters_buf.write(s)

    def _teardown_characters(self):
        """Now that we have the entire string, put it where it needs to go.

 Dispatch to methods like _characters_some_stack_of_tags.  Drop strings
 that are just whitespace.

        """
        if self._characters_buf is None:
            return
        s = self._characters_buf.getvalue()
        if s.strip() == '':
            return
        method_name = '_characters_' + '_'.join(self._tag_stack)
        self._try_calling(method_name, s)

    def _characters_mediawiki_page_title(self, s):
        self._page['title'] = s

    def _characters_mediawiki_page_id(self, s):
        self._page['id'] = s

    def _characters_mediawiki_page_revision_timestamp(self, s):
        self._page['revisions'][-1]['timestamp'] = s

    def _characters_mediawiki_page_revision_contributor_username(self, s):
        self._page['revisions'][-1]['user'] = 'username:' + s

    def _characters_mediawiki_page_revision_contributor_ip(self, s):
        self._page['revisions'][-1]['user'] = 'ip:' + s


def parsewpxml(file, page_handler):
    """Call WPXMLHandler.

    file
        This is the name of the file to parse.

    page_handler
        See WPXMLHandler.__init__.

    """
    parser = make_parser()
    wpxmlhandler = WPXMLHandler(page_handler)
    parser.setContentHandler(wpxmlhandler)
    parser.parse(file)


def main(argv=None,  # Defaults to sys.argv.
         input=sys.stdin, _open=open):

    """Run the application.

    The arguments are really there for dependency injection.

    """

    def page_handler(page):
        """Write the right bits to the right files."""
        try:
            print(page['id'], page['title'])
            # atoms_writer.writerow((page['id'], page['title']))
            for rev in page['revisions']:
                if not 'user' in rev:
                    continue
                print(rev['user'], rev['timestamp'], page['id'])
                # triplets_writer.writerow(
                #     (rev['user'], rev['timestamp'], page['id']))
        except Exception as e:
            print >> sys.stderr, "%s: %s\n%s" % (parser.get_prog_name(),
                                                 e, page)

    global parser
    parser = OptionParser()
    parser.add_option('--atoms', dest='atoms',
        help="store atom ids and names in this file",
        metavar='FILE.tsv')
    parser.add_option('--user-timestamp-atom-triplets',
        dest='user_timestamp_atom_triplets',
        help="store (user, timestamp, atom) triplets in this file",
        metavar='FILE.tsv')
    (options, args) = parser.parse_args(args=argv)
    if args:
        parser.error("No arguments expected")
    for required in ('atoms', 'user_timestamp_atom_triplets'):
        if not getattr(options, required):
            parser.error('The %s parameter is required' % required)

    LINE_BUFFERED = 1
    with closing(_open(options.atoms, 'w', LINE_BUFFERED)) as atoms_file:
        with closing(_open(options.user_timestamp_atom_triplets,
                           'w', LINE_BUFFERED)) as triplets_file:
            # atoms_writer = create_default_writer(atoms_file)
            # triplets_writer = create_default_writer(triplets_file)
            parsewpxml(input, page_handler)


if __name__ == '__main__':

    main()

def test_main():

    """Testing the main method involves a fair bit of dependency injection."""

    class UnclosableStringIO(StringIO):

        """This is a StringIO that ignores the close method."""

        def close(self):
            pass

    def _open(name, *args):
        """Return StringIO() buffers instead of real open file handles."""
        if name == 'atoms.tsv':
            return atoms_file
        elif name == 'triplets.tsv':
            return triplets_file
        else:
            raise ValueError

    atoms_file = UnclosableStringIO()
    triplets_file = UnclosableStringIO()
    parsewpxml.main(
        argv=['--atoms=atoms.csv',
              '--user-timestamp-atom-triplet=triplets.csv'],
        input=open("test_data.xml"),
        _open=_open)