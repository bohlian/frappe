# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
def execute():
	import webnotes
	from webnotes.model import delete_doc
	delete_doc('DocType', 'About Us Team')
	delete_doc('DocType', 'About Us Settings')
	delete_doc('DocType', 'Contact Us Settings')