# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, flt


from frappe.model.document import Document

class PackedItem(Document):
	pass

def get_product_bundle_items(item_code):
	return frappe.db.sql("""select t1.item_code, t1.qty, t1.uom
		from `tabProduct Bundle Item` t1, `tabProduct Bundle` t2
		where t2.new_item_code=%s and t1.parent = t2.name""", item_code, as_dict=1)

def get_packing_item_details(item):
	return frappe.db.sql("""select item_name, description, stock_uom from `tabItem`
		where name = %s""", item, as_dict = 1)[0]

def get_bin_qty(item, warehouse):
	det = frappe.db.sql("""select actual_qty, projected_qty from `tabBin`
		where item_code = %s and warehouse = %s""", (item, warehouse), as_dict = 1)
	return det and det[0] or frappe._dict()

def update_packing_list_item(doc, packing_item_code, qty, main_item_row):
	bin = get_bin_qty(packing_item_code, main_item_row.warehouse)
	item = get_packing_item_details(packing_item_code)

	# check if exists
	exists = 0
	for d in doc.get("packed_items"):
		if d.parent_item == main_item_row.item_code and d.item_code == packing_item_code and d.parent_detail_docname == main_item_row.name:
			pi, exists = d, 1
			break

	if not exists:
		pi = doc.append('packed_items', {})

	pi.parent_item = main_item_row.item_code
	pi.item_code = packing_item_code
	pi.item_name = item.item_name
	pi.parent_detail_docname = main_item_row.name
	pi.description = item.description
	pi.uom = item.stock_uom
	pi.qty = flt(qty)
	pi.actual_qty = flt(bin.get("actual_qty"))
	pi.projected_qty = flt(bin.get("projected_qty"))
	if not pi.warehouse:
		pi.warehouse = main_item_row.warehouse
	if not pi.batch_no:
		pi.batch_no = cstr(main_item_row.get("batch_no"))
	if not pi.target_warehouse:
		pi.target_warehouse = main_item_row.get("target_warehouse")

def make_packing_list(doc):
	"""make packing list for Product Bundle item"""

	if doc.get("_action") and doc._action == "update_after_submit": return

	parent_items = []
	for d in doc.get("items"):
		if frappe.db.get_value("Product Bundle", {"new_item_code": d.item_code}):
			for i in get_product_bundle_items(d.item_code):
				update_packing_list_item(doc, i.item_code, flt(i.qty)*flt(d.qty), d)

			if [d.item_code, d.name] not in parent_items:
				parent_items.append([d.item_code, d.name])

	cleanup_packing_list(doc, parent_items)

def cleanup_packing_list(doc, parent_items):
	"""Remove all those child items which are no longer present in main item table"""
	delete_list = []
	for d in doc.get("packed_items"):
		if [d.parent_item, d.parent_detail_docname] not in parent_items:
			# mark for deletion from doclist
			delete_list.append(d)

	if not delete_list:
		return doc

	packed_items = doc.get("packed_items")
	doc.set("packed_items", [])
	for d in packed_items:
		if d not in delete_list:
			doc.append("packed_items", d)
