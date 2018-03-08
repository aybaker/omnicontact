#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":

    if sys.version_info[0] != 2 or sys.version_info[1] != 7:
        print ""
        print " ERROR:"
        print "   Debe usar Python 2.7"
        print ""
        sys.exit(1)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fts_web.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
