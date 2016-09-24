# Copyright (c) 2013, frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe import utils
from frappe.utils import flt
from datetime import datetime,timedelta
import operator
#import timedelta
#import json

def execute(filters=None):
	columns = get_columns()
	report_entries = get_report_entries(filters)
	data = []
	
	

	for sle in report_entries:

		
		todate_round=get_round(sle.section_id,filters)
		section_detail = get_section_details(sle.section_id,filters)
		
		to_date=get_to_date(sle.section_id,filters)
		from_date=get_from_date(sle.section_id,filters)
		act=get_actual_to_date_green_leaf(sle.section_id,filters)
		bud=get_to_date_budget(sle.section_id,filters)
		perc=get_plus_minus_percentage(sle.section_id,filters)
		done_or_not_done=find_round(sle.section_id,filters)
		act1=get_actual_gree_leaf(sle.section_id,filters)
		data.append([sle.division_name,sle.section_id,sle.section_name,section_detail,todate_round,from_date,to_date,act,bud,perc,done_or_not_done,act1])
		
	return columns, data


	


# , sle.section_area, sle.area, sle.prune_type, sle.bush_type


def get_report_entries(filters):
	return frappe.db.sql("""select distinct section_id,section_name,division_name from `tabDaily Green Leaf in details` where estate_name = %s and prune_type=%s and bush_type=%s and date BETWEEN %s AND %s ORDER BY section_id ASC""",(filters.estate_name,filters.prune_type,filters.bush_type,'2016-01-01', filters.date),as_dict=1)

def get_section_details(section_id,filters):
	return frappe.db.sql("""select min(section_area) from `tabDaily Green Leaf in details` where section_id = %s and date BETWEEN %s and %s""",(section_id,'2016-01-01',filters.date)) 


def get_round(section_id,filters):
	return frappe.db.sql("""select sum(area)/section_area from `tabDaily Green Leaf in details` where section_id = %s and date BETWEEN %s AND %s ORDER BY date DESC LIMIT 1 """,(section_id, '2016-01-01',filters.date))

def find_round(section_id,filters):
	todate_round=get_round(section_id,filters)
	if todate_round[0][0].is_integer():
		return "complete"
	else:
		return "incomplete"


def get_to_date(section_id,filters):
	date1=frappe.db.sql("""select max(date) from `tabDaily Green Leaf in details` where section_id = %s and date between %s and %s""",(section_id,'2016-01-01',filters.date))
	single_day=find_round(section_id,filters)
	if single_day=="complete":
		to=date1
	else:
		to=frappe.db.sql("""select max(date) from `tabDaily Green Leaf in details` where section_id = %s and date<%s""",(section_id,date1))
	return to	


def get_from_date(section_id,filters):
	date1=get_to_date(section_id,filters) 
	area_plucked=frappe.db.sql("""select area from `tabDaily Green Leaf in details` where section_id=%s and date=%s """,(section_id,date1))
	actual_area=get_section_details(section_id,filters)
	if area_plucked==actual_area:
		frm=date1
	elif area_plucked<actual_area:
		frm=0
		yesterday=datetime.strptime(date1[0][0],'%Y-%m-%d')-timedelta(days=1)
		date2=yesterday.date()
		area_plucked_prev=frappe.db.sql("""select area from `tabDaily Green Leaf in details` where section_id=%s and date=%s """,(section_id,date2))
		if area_plucked_prev:
			for i in range(0,len(area_plucked)):
				for j in range(0,len(area_plucked_prev)):
					total=round((area_plucked_prev[0][j]+area_plucked[0][i]),2)
					if total-actual_area[0][0]==0:
						frm=date2
					else:
						date3=date2-timedelta(days=1)
						frm=date3
						
					
	return frm


			
def get_actual_to_date_green_leaf(section_id,filters):

	date2=get_from_date(section_id,filters)
	date1=get_to_date(section_id,filters)
	day=find_round(section_id,filters)
	if day=="complete":
		
		leaf_c=frappe.db.sql("""select round(sum(leaf_count),0) from `tabDaily Green Leaf in details` where section_id = %s and date between %s and %s""",(section_id,date2,filters.date))
		a=frappe.db.sql("""select section_area from `tabDaily Green Leaf in details` where section_id = %s """,(section_id))
		act=round(leaf_c[0][0]/a[0][0],0)
	else:
		leaf_c=frappe.db.sql("""select round(sum(leaf_count),0) from `tabDaily Green Leaf in details` where section_id = %s and date between %s and %s""",(section_id,date2,date1))
		a=frappe.db.sql("""select section_area from `tabDaily Green Leaf in details` where section_id = %s """,(section_id))
		act=round(leaf_c[0][0]/a[0][0],0)
	return act

def get_to_date_budget(section_id,filters):
	date1=get_to_date(section_id,filters)
	return frappe.db.sql("""select round(((t.round_days*p.august)/(0.225*31)),0) from `tabDaily Green Leaf in details` t INNER JOIN `tabPruning Cycle` p  ON t.section_id=p.section_id where t.section_id = %s and t.date=%s""",(section_id,date1)) 
	

def get_plus_minus_percentage(section_id,filters):
	act=get_actual_to_date_green_leaf(section_id,filters)
	bud=get_to_date_budget(section_id,filters)
	perc=round((act-bud[0][0])*100/bud[0][0],2)
	return perc

	
def get_actual_gree_leaf(section_id,filters):
	date2=get_from_date(section_id,filters)
	date1=get_to_date(section_id,filters)
	day=find_round(section_id,filters)
	if day=="complete":
		
		leaf_c=frappe.db.sql("""select round(sum(leaf_count),0) from `tabDaily Green Leaf in details` where section_id = %s and date between %s and %s""",(section_id,'2016-01-01',filters.date))
		a=frappe.db.sql("""select section_area from `tabDaily Green Leaf in details` where section_id = %s """,(section_id))
		act=round(leaf_c[0][0]/a[0][0],0)
	else:
		leaf_c=frappe.db.sql("""select round(sum(leaf_count),0) from `tabDaily Green Leaf in details` where section_id = %s and date between %s and %s""",(section_id,date2,date1))
		a=frappe.db.sql("""select section_area from `tabDaily Green Leaf in details` where section_id = %s """,(section_id))
		act=round(leaf_c[0][0]/a[0][0],0)
	return round(act*0.225,0)




def get_sle_conditions(filters):
	conditions = []
	return "and {}".format(" and ".join(conditions)) if conditions else ""



def get_columns():
		
		columns = [{
			"fieldname": "division_name",
				"label": _("Division"),
				"fieldtype": "Link",
				"options": "Division",
				"width": 80

		}]

		columns.append({
				"fieldname": "section_id",
				"label": _("Section Id"),
				"fieldtype": "Link",
				"options": "Section",
				"width": 90
	    })

		columns.append({
				"fieldname": "section_name",
				"label": _("Section Name"),
				"fieldtype": "Link",
				"options": "Section",
				"width": 90
	    })
		
		columns.append({
				"fieldname": "original_area",
				"label": _("Area"),
				"fieldtype": "round(Float,2)",
				"options": "daily_green_leaf_in_details",
				"width": 70
	    })


		
		columns.append({
			"label": _("Round"),
			"fieldtype": "round(Float,5)",
			"width":71
		})

		columns.append({
			"label": _("From"),
			"fieldtype": "Data",
			"width":100
		})

		
		columns.append({
			"label": _("To"),
			"fieldtype": "Data",
			"width":100
		})

		columns.append({
			"label": _("Act"),
			"fieldtype": "round(float,0)",
			"width":71
		})

		columns.append({
			"label": _("Bud"),
			"fieldtype": "round(float,0)",
			"width":71
		})

		columns.append({
			"label": _("+/- %"),
			"fieldtype": "data",
			"width":71
		})

		columns.append({
			"label": _("done or not done"),
			"fieldtype": "data",
			"width":71
		})

		columns.append({
			"label": _("Actual"),
			"fieldtype": "round(float,0)",
			"width":71
		})


		
		return columns

	