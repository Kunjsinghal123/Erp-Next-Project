app_name = "gdl_pms"
app_title = "GDL PMS"
app_publisher = "GDL"
app_description = "GDL PMS"
app_email = "admin@gdl.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "gdl_pms",
		"logo": "/assets/gdl_pms/logo_gdl.png",
		"title": "GDL PMS",
		"route": "/app/gdl-pms",
	}
]
app_logo_url = "/assets/gdl_pms/logo_gdl.png"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/gdl_pms/css/gdl_pms_theme.bundle.css",
	"/assets/gdl_pms/css/gdl_pms.css"
]
app_include_js = [
	"/assets/gdl_pms/js/pms_employee_dashboard.js",
	"/assets/gdl_pms/js/pms_supervisor_dashboard.js",
	"/assets/gdl_pms/js/pms_reviewer_dashboard.js",
	"/assets/gdl_pms/js/pms_hr_dashboard.js",
	"/assets/gdl_pms/js/pms_supervisor_2_dashboard.js",
	"/assets/gdl_pms/js/pms_router_guard.js"
]

# include js, css files in header of web template
web_include_css = [
	"/assets/gdl_pms/css/gdl_pms_theme.bundle.css",
	"/assets/gdl_pms/css/gdl_pms.css"
]

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "login"

# website user home page (by Role)
role_home_page = {
	"HR Admin": "desk/pms-hr",
	"Reviewer": "desk/pms-reviewer",
	"Supervisor 2": "desk/pms-supervisor-2",
	"Supervisor": "desk/pms-supervisor",
	"Employee": "desk/pms-employee"
}

on_session_creation = "gdl_pms.auth_hooks.on_session_creation"
boot_session = "gdl_pms.auth_hooks.boot_session"

doc_events = {
	"User": {
		"validate": "gdl_pms.auth_hooks.set_user_default_workspace"
	}
}


# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "gdl_pms.utils.jinja_methods",
# 	"filters": "gdl_pms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "gdl_pms.install.before_install"
# after_install = "gdl_pms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "gdl_pms.uninstall.before_uninstall"
# after_uninstall = "gdl_pms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "gdl_pms.utils.before_app_install"
# after_app_install = "gdl_pms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "gdl_pms.utils.before_app_uninstall"
# after_app_uninstall = "gdl_pms.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "gdl_pms.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "gdl_pms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"PMS Appraisal Cycle": "gdl_pms.gdl_pms.doctype.pms_appraisal_cycle.pms_appraisal_cycle.get_permission_query_conditions",
	"PMS Appraisal": "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.get_permission_query_conditions",
	"PMS Plan Amendment": "gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment.get_permission_query_conditions",
	"PMS Calendar": "gdl_pms.gdl_pms.doctype.pms_calendar.pms_calendar.get_permission_query_conditions",
}

has_permission = {
	"PMS Appraisal Cycle": "gdl_pms.gdl_pms.doctype.pms_appraisal_cycle.pms_appraisal_cycle.has_permission",
	"PMS Appraisal": "gdl_pms.gdl_pms.doctype.pms_appraisal.pms_appraisal.has_permission",
	"PMS Plan Amendment": "gdl_pms.gdl_pms.doctype.pms_plan_amendment.pms_plan_amendment.has_permission",
	"PMS Calendar": "gdl_pms.gdl_pms.doctype.pms_calendar.pms_calendar.has_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee": {
		"on_update": "gdl_pms.employee_hooks.auto_assign_roles"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"gdl_pms.tasks.send_pending_action_reminders"
	],
	"cron": {
		"0 6 * * *": [
			"gdl_pms.tasks.auto_transition_cycle_states"
		]
	}
}

# Testing
# -------

# before_tests = "gdl_pms.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "gdl_pms.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "gdl_pms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "gdl_pms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["gdl_pms.utils.before_request"]
# after_request = ["gdl_pms.utils.after_request"]

# Job Events
# ----------
# before_job = ["gdl_pms.utils.before_job"]
# after_job = ["gdl_pms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"gdl_pms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

