==============
Foreign Effigy
==============

Foreign Effigy (fe) is a tool that downloads energy usage data from a well
known Australian energy provider. The providers name sounds like *Foreign
Effigy*.

Currently fe is very bare bones and simply downloads data for a date range and
stores it in an sqlite3 database. Time permitting, I'm planning to add a few
more features.

First, you need the contract id of your service you want fe to download the
data for. It should be a 10 digit int.

Then, build the virtualenv::

    $ make

Create a fe.ini file with your contract id as the section and username and
password key/values.

Run the script, swapping out the appropriate params::

    $ venv/bin/python foreigneffigy/foreigneffigy.py \
        --conf-file=fe.ini \
        --db-file=fe.db \
        --start-date=2017-01-01 \
        --end-date=2017-01-31

You should have an sqlite3 file called fe.db with your data. Enjoy!
