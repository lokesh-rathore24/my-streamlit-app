"""
Activity Config Admin Panel -- Streamlit Wireframe
===================================================
Design-only prototype. All data lives in st.session_state.
Run: .venv/bin/streamlit run admin_wireframe.py
"""

import copy
import json
import streamlit as st

# ---------------------------------------------------------------------------
# Constants / Registries
# ---------------------------------------------------------------------------

RESPONSE_TYPES = ["deep_link", "phone_call", "form_input", "confirmation_popup", "toast"]

PRE_HANDLERS = [
    "Generic (auto-resolved by response_type)",
    "WhatsappPreHandler",
    "ChoosePlanPreHandler",
    "CreateOpportunityPreHandler",
    "ProductBrochureSpecPreHandler",
    "CustPresentationSpecPreHandler",
    "MktgCollateralSpecPreHandler",
    "VerifyOpportunitiesPreHandler",
    "ConfirmQuotePreHandler",
    "UploadToLSQPreHandler",
    "CreateBIPreHandler",
    "EditBIPreHandler",
    "AthenaOnboardPreHandler",
    "UpdateFromAthenaPreHandler",
    "+ Custom (enter class name)",
]

POST_HANDLERS = [
    "GenericToastPostHandler (default)",
    "MarkAsLostPostHandler",
    "CreateOpportunityPostHandler",
    "ProductBrochureSpecPostHandler",
    "CustPresentationSpecPostHandler",
    "MktgCollateralSpecPostHandler",
    "VerifyOpportunitiesPostHandler",
    "CreateBIPostHandler",
    "AthenaOnboardPostHandler",
    "+ Custom (enter class name)",
]

GENERIC_PRE_MAP = {
    "deep_link": "GenericRedirectPreHandler",
    "phone_call": "GenericRedirectPreHandler",
    "form_input": "GenericFormPreHandler",
    "confirmation_popup": "GenericConfirmationPreHandler",
    "toast": "GenericDirectActionPreHandler",
}

INTEGRATION_EVENTS = [
    "lsq_capture_opportunity",
    "lsq_create_activity",
    "athena_add_lead",
    "athena_add_proposal",
    "athena_upload_document",
    "athena_get_proposal_status",
]

INTEGRATION_PHASES = ["pre", "post"]
INTEGRATION_TRIGGERS = ["on_success", "on_failure", "always"]
INTEGRATION_MODES = ["blocking", "fire_and_forget"]

FIELD_TYPES = ["text", "dropdown", "number", "date", "textarea"]
OPTIONS_SOURCES = ["products_list", "reportees_list", "stages_list", "+ Custom"]
TOAST_TYPES = ["error", "success", "warning"]

ENTITY_TYPES = ["Lead", "Contact", "LeadProduct", "Quote", "User", "ContactOrg"]

ENTITY_SYSTEM_FIELDS = {
    "Lead": ["external_id", "lead_source", "lead_campaign", "deal_value", "is_verified", "closure_probability_value"],
    "Contact": ["external_contact_id", "salutation", "first_name", "last_name", "primary_email",
                 "primary_mobile_number", "alternate_mobile_number", "alternate_email", "contact_org_id", "address_id"],
    "LeadProduct": ["lead_product_status"],
    "Quote": [],
    "User": [],
    "ContactOrg": [],
}

ENTITY_ID_HINTS = {
    "Lead": "lead_id",
    "Contact": "lead_summary.data.contact.id",
    "LeadProduct": "lead_product_id",
    "Quote": "quote_id",
    "User": "user_id",
    "ContactOrg": "lead_summary.data.contact_org.id",
}

BADGE_COLORS = {
    "deep_link": "#1E88E5",
    "phone_call": "#43A047",
    "form_input": "#FB8C00",
    "confirmation_popup": "#8E24AA",
    "toast": "#E53935",
}

# ---------------------------------------------------------------------------
# Seed Data: Validation Rules
# ---------------------------------------------------------------------------

SEED_VALIDATION_RULES = {
    "lead_summary_exists": {
        "name": "lead_summary_exists",
        "expression": "$exists(lead_summary.data)",
        "error_title": "Could not find required details",
        "error_subtitle": "Lead details not found",
        "error_toast_type": "error",
    },
    "contact_exists": {
        "name": "contact_exists",
        "expression": "$exists(lead_summary.data.contact)",
        "error_title": "Could not find required details",
        "error_subtitle": "Contact details not found",
        "error_toast_type": "error",
    },
    "contact_has_phone": {
        "name": "contact_has_phone",
        "expression": "$exists(lead_summary.data.contact.primary_mobile_number)",
        "error_title": "Could not find required details",
        "error_subtitle": "Phone number not found",
        "error_toast_type": "error",
    },
    "product_is_active": {
        "name": "product_is_active",
        "expression": "product_data.data.is_active = true",
        "error_title": "Action failed",
        "error_subtitle": "This product is no longer active",
        "error_toast_type": "error",
    },
    "product_has_bi_deeplink": {
        "name": "product_has_bi_deeplink",
        "expression": "$exists(product_data.data.product_bi_deeplink)",
        "error_title": "Create quote failed",
        "error_subtitle": "Quote link not available for this product",
        "error_toast_type": "error",
    },
    "product_has_salesbundle": {
        "name": "product_has_salesbundle",
        "expression": "$exists(product_data.data.product_salesbundle)",
        "error_title": "Action failed",
        "error_subtitle": "Product brochure not found",
        "error_toast_type": "error",
    },
    "lead_is_verified": {
        "name": "lead_is_verified",
        "expression": '$lowercase(lead_summary.data.custom_fields.verification_status) = "verified"',
        "error_title": "Action failed",
        "error_subtitle": "Verify opportunity before proceeding",
        "error_toast_type": "error",
    },
    "lead_not_verified": {
        "name": "lead_not_verified",
        "expression": '$lowercase(lead_summary.data.custom_fields.verification_status) != "verified"',
        "error_title": "Opportunity already verified",
        "error_subtitle": "",
        "error_toast_type": "error",
    },
    "lead_not_lost": {
        "name": "lead_not_lost",
        "expression": "lead_summary.data.custom_fields.is_lost != true",
        "error_title": "Action failed",
        "error_subtitle": "This opportunity is marked as lost",
        "error_toast_type": "error",
    },
    "quote_id_present": {
        "name": "quote_id_present",
        "expression": "$exists(quote_id) and quote_id != null",
        "error_title": "Action failed",
        "error_subtitle": "Quote ID not provided",
        "error_toast_type": "error",
    },
    "lead_product_id_present": {
        "name": "lead_product_id_present",
        "expression": "$exists(lead_product_id) and lead_product_id != null",
        "error_title": "Action failed",
        "error_subtitle": "Lead Product ID not provided",
        "error_toast_type": "error",
    },
    "product_id_present": {
        "name": "product_id_present",
        "expression": "$exists(product_id) and product_id != null",
        "error_title": "Action failed",
        "error_subtitle": "Product ID not provided",
        "error_toast_type": "error",
    },
}

# ---------------------------------------------------------------------------
# Seed Data: 20 Activity Configs
# ---------------------------------------------------------------------------

SEED_ACTIVITIES = {
    "Call": {
        "response_type": "phone_call",
        "is_two_step": False,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": ["lead_summary_exists", "contact_exists", "contact_has_phone"],
        "post_validation_rules": None,
        "response_config": {"display_text": "Call Initiated"},
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Whatsapp": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": "WhatsappPreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": ["lead_summary_exists", "contact_exists", "contact_has_phone"],
        "post_validation_rules": None,
        "response_config": {"display_text": "Whatsapp Initiated"},
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Visiting Card": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/app/#/dvc",
            "display_text": "Visiting card link accessed",
            "success_title": "Success",
            "success_subtitle": "Visiting Card shared",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Mark as Lost": {
        "response_type": "confirmation_popup",
        "is_two_step": True,
        "pre_handler_ref": None,
        "post_handler_ref": "MarkAsLostPostHandler",
        "pre_validation_rules": ["lead_summary_exists", "lead_not_lost"],
        "post_validation_rules": None,
        "response_config": {
            "popup_title": "Mark as lost",
            "success_button_label": "Confirm",
            "cancel_button_label": "Cancel",
            "popup_subtitle": "Are you sure you want to mark the opportunity as lost?",
            "description": "Once an opportunity is marked as lost, it cannot be restored.",
            "success_title": "Opportunity marked as lost successfully",
            "success_subtitle": "",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Product Brochure": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/app/#/productBundle/-1",
            "display_text": "Product Brochure Redirection",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Customer Presentation": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/app/#/productPresentationInput/-1?presentationId=1&presentationName&inputOne&inputTwo",
            "display_text": "Product Presentation",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Marketing Collateral": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/app/#/mcDirectory/1?isTwoTierDirectory=true&isFirstDirectoryPage=true",
            "display_text": "Marketing Collatoral",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Open Athena": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": None,
        "post_handler_ref": None,
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "url_template": "https://avivauat-v2.salesdrive.app/login",
            "display_text": "Athena opened",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Choose Plan": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": "ChoosePlanPreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": ["lead_summary_exists"],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/app/#/biplanlist",
            "display_text": "Choose Plan Redirection Successful",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Add new opportunity": {
        "response_type": "form_input",
        "is_two_step": True,
        "pre_handler_ref": "CreateOpportunityPreHandler",
        "post_handler_ref": "CreateOpportunityPostHandler",
        "pre_validation_rules": None,
        "post_validation_rules": None,
        "response_config": {
            "popup_title": "Add new opportunity",
            "success_button_label": "Submit",
            "cancel_button_label": "Cancel",
            "close_button_visible": True,
            "fields": [
                {"name": "opportunity_name", "label": "Opportunity Name", "type": "text", "regex": r"^(?!\s*$)[a-zA-Z\s]{1,50}$", "required": True},
                {"name": "phone_number", "label": "Phone Number", "type": "text", "regex": r"^[0-9]{10}$", "required": True},
                {"name": "product", "label": "Product interested", "type": "dropdown", "required": False, "options_source": "products_list"},
            ],
            "display_text": "Preparing create opportunity form",
            "success_title": "Opportunity created successfully",
            "success_subtitle": "",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Product Brochure - Specfic": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": "ProductBrochureSpecPreHandler",
        "post_handler_ref": "ProductBrochureSpecPostHandler",
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Product brochure redirection failed", "error_subtitle": "This product is no longer active"},
            {"rule": "product_has_salesbundle", "error_title": "Product brochure redirection failed", "error_subtitle": "This product brochure is not found"},
        ],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/{product_data.data.product_salesbundle}",
            "display_text": "Product brochure link accessed",
            "success_title": "Product brochure shared",
            "success_subtitle": "Product brochure shared successfully",
        },
        "integration_config": [
            {"event": "lsq_create_activity", "phase": "post", "trigger": "on_success", "mode": "fire_and_forget", "fail_on_error": False, "params": {"activity_event": 239, "note_template": "Product Brochure Shared: {signal_data.plugin_name}"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Customer Presentation - Specific": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": "CustPresentationSpecPreHandler",
        "post_handler_ref": "CustPresentationSpecPostHandler",
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Product presentation access failed", "error_subtitle": "This product is no longer active"},
        ],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/{product_data.data.product_customer_presentation}",
            "display_text": "Product Presentation link accessed",
            "success_title": "Success",
            "success_subtitle": "Activity marked as completed",
        },
        "integration_config": [
            {"event": "lsq_create_activity", "phase": "post", "trigger": "on_success", "mode": "fire_and_forget", "fail_on_error": False, "condition": "$not($lowercase(lead_summary.data.stage.name) in ['lost', 'pushed to athena', 'rejected'])", "params": {"activity_event": 239, "note_template": "Product Presentation Shared: {signal_data.plugin_name}"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Marketing Collateral - Specific": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": "MktgCollateralSpecPreHandler",
        "post_handler_ref": "MktgCollateralSpecPostHandler",
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Marketing collateral access failed", "error_subtitle": "This product is no longer active"},
        ],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}/{product_data.data.product_marketing_collateral}",
            "display_text": "Marketing collateral link accessed",
            "success_title": "Success",
            "success_subtitle": "Activity marked as completed",
        },
        "integration_config": [
            {"event": "lsq_create_activity", "phase": "post", "trigger": "on_success", "mode": "fire_and_forget", "fail_on_error": False, "condition": "$not($lowercase(lead_summary.data.stage.name) in ['lost', 'pushed to athena', 'rejected'])", "params": {"activity_event": 239, "note_template": "Marketing Collatoral Shared: {signal_data.plugin_name}"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Verify Opportunity": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": "VerifyOpportunitiesPreHandler",
        "post_handler_ref": "VerifyOpportunitiesPostHandler",
        "pre_validation_rules": [
            "lead_summary_exists",
            {"rule": "lead_not_verified", "error_title": "Opportunity already verified", "error_subtitle": "", "error_toast_type": "success"},
            {"rule": "contact_exists", "error_title": "Opportunity verification failed", "error_subtitle": "Contact your admin, please try again later(503)"},
            {"rule": "contact_has_phone", "error_title": "Opportunity verification failed", "error_subtitle": "Contact your admin, please try again later(503)"},
        ],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}{VERIFY_OPPORTUNITY_URL}?lead_id={lead_id}&lead_mobile_number={lead_summary.data.contact.primary_mobile_number}&lead_name={lead_summary.data.contact.first_name}&correlation_id={correlation_id}&activity_id={activity_id}",
            "display_text": "Verify Opportunity link accessed",
            "success_title": "Opportunity verified",
            "success_subtitle": "",
        },
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": [
            {"source_expression": "'verified'", "entity": "Lead", "identifier": "lead_id", "destination_property": "verification_status"},
            {"source_expression": "$now()", "entity": "Lead", "identifier": "lead_id", "destination_property": "verification_timestamp"},
        ],
        "use_legacy_script": False,
    },
    "Confirm quote": {
        "response_type": "toast",
        "is_two_step": False,
        "pre_handler_ref": "ConfirmQuotePreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": [
            {"rule": "product_is_active", "error_title": "Confirm quote failed", "error_subtitle": "This product is no longer active"},
            "lead_summary_exists",
            {"rule": "lead_is_verified", "error_title": "Confirm quote failed", "error_subtitle": "Verify opportunity before confirming quote"},
        ],
        "post_validation_rules": None,
        "response_config": {"display_text": "Quote confirmed", "success_title": "Quote confirmed successfully", "success_subtitle": ""},
        "integration_config": [
            {"event": "lsq_create_activity", "phase": "pre", "trigger": "on_success", "mode": "blocking", "fail_on_error": False, "params": {"activity_event": 240, "note_template": "Quote confirmed for {product_data.data.product_name}"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Upload Self Source Lead to LSQ": {
        "response_type": "toast",
        "is_two_step": False,
        "pre_handler_ref": "UploadToLSQPreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": ["lead_summary_exists", "contact_exists", "contact_has_phone"],
        "post_validation_rules": None,
        "response_config": {"display_text": "Opportunity Captured", "success_title": "Success", "success_subtitle": "Opportunity captured successfully"},
        "integration_config": [
            {"event": "lsq_capture_opportunity", "phase": "pre", "trigger": "on_success", "mode": "blocking", "fail_on_error": True, "params": {"search_by": "Phone", "opportunity_event_code": 12000, "status": "Open"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Create Quote": {
        "response_type": "deep_link",
        "is_two_step": True,
        "pre_handler_ref": "CreateBIPreHandler",
        "post_handler_ref": "CreateBIPostHandler",
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Create quote failed", "error_subtitle": "This product is no longer active"},
            "lead_summary_exists",
            {"rule": "product_has_bi_deeplink", "error_title": "Create quote failed", "error_subtitle": "Quote link not available for this product"},
        ],
        "post_validation_rules": None,
        "response_config": {
            "url_template": "{company_url}{product_data.data.product_bi_deeplink}",
            "display_text": "Quote creation in progress",
            "success_title": "Quote Created",
            "success_subtitle": "Quote created successfully",
        },
        "integration_config": [
            {"event": "lsq_capture_opportunity", "phase": "post", "trigger": "on_success", "mode": "fire_and_forget", "fail_on_error": False, "condition": "$not($exists(lead_summary.data.external_id))", "params": {"search_by": "Phone", "opportunity_event_code": 12000, "status": "Open"}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Edit Quote": {
        "response_type": "deep_link",
        "is_two_step": False,
        "pre_handler_ref": "EditBIPreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Edit quote failed", "error_subtitle": "This product is no longer active"},
            "lead_summary_exists",
            {"rule": "lead_is_verified", "error_title": "Edit quote failed", "error_subtitle": "Verify opportunity before editing quote"},
            "quote_id_present",
            {"rule": "product_has_bi_deeplink", "error_title": "Edit quote failed", "error_subtitle": "BI deeplink not available for this product"},
        ],
        "post_validation_rules": None,
        "response_config": {"display_text": "Edit Quote Redirection Successful"},
        "integration_config": None,
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
    "Onboard": {
        "response_type": "form_input",
        "is_two_step": True,
        "pre_handler_ref": "AthenaOnboardPreHandler",
        "post_handler_ref": "AthenaOnboardPostHandler",
        "pre_validation_rules": [
            "product_id_present",
            {"rule": "product_is_active", "error_title": "Onboarding failed", "error_subtitle": "This product is no longer active"},
            "lead_summary_exists",
            "quote_id_present",
            "lead_product_id_present",
        ],
        "post_validation_rules": None,
        "response_config": {
            "popup_title": "Onboard",
            "success_button_label": "Save",
            "cancel_button_label": "Cancel",
            "fields": [{"name": "reportee", "label": "Select Owner", "type": "dropdown", "required": True, "options_source": "reportees_list"}],
            "display_text": "Onboarding in progress",
            "success_title": "Opportunity onboarded successfully",
            "success_subtitle": "",
        },
        "integration_config": [
            {"event": "athena_add_lead", "phase": "pre", "trigger": "on_success", "mode": "blocking", "fail_on_error": True, "params": {}},
            {"event": "athena_add_proposal", "phase": "post", "trigger": "on_success", "mode": "blocking", "fail_on_error": True, "condition": "payload.is_submitted = true", "params": {}},
            {"event": "athena_upload_document", "phase": "post", "trigger": "on_success", "mode": "blocking", "fail_on_error": False, "condition": "$exists(integration_results.athena_add_proposal.data.transaction_id)", "params": {}},
            {"event": "athena_get_proposal_status", "phase": "post", "trigger": "on_success", "mode": "blocking", "fail_on_error": False, "params": {}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": [
            {"source_expression": "handler_result.payload.proposal_number", "entity": "Lead", "identifier": "lead_id", "destination_property": "Proposal Number"},
            {"source_expression": "'Pushed to Athena'", "entity": "Lead", "identifier": "lead_id", "destination_property": "AthenaStatus"},
            {"source_expression": "handler_result.payload.athena_owner", "entity": "Lead", "identifier": "lead_id", "destination_property": "Athena Owner"},
        ],
        "use_legacy_script": False,
    },
    "Update": {
        "response_type": "toast",
        "is_two_step": False,
        "pre_handler_ref": "UpdateFromAthenaPreHandler",
        "post_handler_ref": None,
        "pre_validation_rules": ["lead_summary_exists"],
        "post_validation_rules": None,
        "response_config": {"display_text": "Athena status fetched successfully", "success_title": "Status fetched successfully", "success_subtitle": ""},
        "integration_config": [
            {"event": "athena_get_proposal_status", "phase": "pre", "trigger": "on_success", "mode": "blocking", "fail_on_error": True, "params": {}},
        ],
        "pre_entity_updates": None,
        "post_entity_updates": None,
        "use_legacy_script": False,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def badge(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.78em;font-weight:600;">{text}</span>'
    )


def handler_display(ref):
    if ref is None:
        return "Generic (auto)"
    return ref


def _rule_name(r):
    if isinstance(r, str):
        return r
    return r.get("rule", "?")


def count_integrations(cfg):
    ic = cfg.get("integration_config")
    return len(ic) if ic else 0


def count_entity_updates(cfg):
    pre = cfg.get("pre_entity_updates") or []
    post = cfg.get("post_entity_updates") or []
    return len(pre) + len(post)


def init_state():
    if "activities" not in st.session_state:
        st.session_state.activities = copy.deepcopy(SEED_ACTIVITIES)
    if "validation_rules" not in st.session_state:
        st.session_state.validation_rules = copy.deepcopy(SEED_VALIDATION_RULES)
    if "current_page" not in st.session_state:
        st.session_state.current_page = "list"
    if "selected_activity" not in st.session_state:
        st.session_state.selected_activity = None


def navigate(page, activity=None):
    st.session_state.current_page = page
    st.session_state.selected_activity = activity


def build_config_json(name, cfg):
    """Build the JSON representation as it would be stored in the DB."""
    out = {
        "activity_name": name,
        "response_type": cfg["response_type"],
        "is_two_step": cfg["is_two_step"],
        "pre_handler_ref": cfg["pre_handler_ref"],
        "post_handler_ref": cfg["post_handler_ref"],
        "pre_validation_rules": cfg["pre_validation_rules"],
        "post_validation_rules": cfg["post_validation_rules"],
        "response_config": cfg["response_config"],
        "integration_config": cfg["integration_config"],
        "pre_entity_updates": cfg.get("pre_entity_updates"),
        "post_entity_updates": cfg.get("post_entity_updates"),
        "use_legacy_script": cfg["use_legacy_script"],
    }
    return json.dumps(out, indent=2, default=str)


# ---------------------------------------------------------------------------
# Page 1: Activity List
# ---------------------------------------------------------------------------

def page_activity_list():
    st.markdown("## Activity Configurations")

    activities = st.session_state.activities

    # --- Stats bar ---
    total = len(activities)
    config_driven = sum(1 for c in activities.values() if not c.get("use_legacy_script"))
    custom_handlers = sum(1 for c in activities.values() if c.get("pre_handler_ref") is not None)
    with_integrations = sum(1 for c in activities.values() if count_integrations(c) > 0)
    with_entity_updates = sum(1 for c in activities.values() if count_entity_updates(c) > 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Activities", total)
    c2.metric("Config-Driven", config_driven)
    c3.metric("Custom Handlers", custom_handlers)
    c4.metric("With Integrations", with_integrations)
    c5.metric("With Entity Updates", with_entity_updates)

    st.divider()

    # --- Filters ---
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 2])
    search = fc1.text_input("Search", placeholder="Filter by name...", label_visibility="collapsed")
    filter_rt = fc2.selectbox("Response Type", ["All"] + RESPONSE_TYPES, key="filter_rt")
    filter_step = fc3.selectbox("Steps", ["All", "Single-step", "Two-step"], key="filter_step")
    filter_int = fc4.selectbox("Integrations", ["All", "Has integrations", "No integrations"], key="filter_int")

    # --- Filter logic ---
    filtered = {}
    for name, cfg in activities.items():
        if search and search.lower() not in name.lower():
            continue
        if filter_rt != "All" and cfg["response_type"] != filter_rt:
            continue
        if filter_step == "Single-step" and cfg["is_two_step"]:
            continue
        if filter_step == "Two-step" and not cfg["is_two_step"]:
            continue
        if filter_int == "Has integrations" and count_integrations(cfg) == 0:
            continue
        if filter_int == "No integrations" and count_integrations(cfg) > 0:
            continue
        filtered[name] = cfg

    # --- New Activity button ---
    if st.button("+ New Activity", type="primary"):
        navigate("editor", "__new__")
        st.rerun()

    st.markdown("")

    # --- Table header ---
    cols = st.columns([3, 2, 1.2, 2.5, 2.5, 1.5, 1.5, 1])
    cols[0].markdown("**Activity Name**")
    cols[1].markdown("**Response Type**")
    cols[2].markdown("**Steps**")
    cols[3].markdown("**Pre Handler**")
    cols[4].markdown("**Post Handler**")
    cols[5].markdown("**Integrations**")
    cols[6].markdown("**Entity Updates**")
    cols[7].markdown("**Edit**")

    st.divider()

    # --- Table rows ---
    for name, cfg in filtered.items():
        cols = st.columns([3, 2, 1.2, 2.5, 2.5, 1.5, 1.5, 1])
        cols[0].markdown(f"**{name}**")
        rt = cfg["response_type"]
        cols[1].markdown(badge(rt, BADGE_COLORS.get(rt, "#666")), unsafe_allow_html=True)
        cols[2].markdown("Two-step" if cfg["is_two_step"] else "Single")
        cols[3].markdown(f"`{handler_display(cfg['pre_handler_ref'])}`")
        if cfg["is_two_step"]:
            cols[4].markdown(f"`{handler_display(cfg['post_handler_ref'])}`")
        else:
            cols[4].markdown("--")
        ic = count_integrations(cfg)
        if ic > 0:
            cols[5].markdown(badge(f"{ic} event{'s' if ic > 1 else ''}", "#546E7A"), unsafe_allow_html=True)
        else:
            cols[5].markdown("--")
        eu = count_entity_updates(cfg)
        if eu > 0:
            cols[6].markdown(badge(f"{eu} rule{'s' if eu > 1 else ''}", "#6A1B9A"), unsafe_allow_html=True)
        else:
            cols[6].markdown("--")
        if cols[7].button("Edit", key=f"edit_{name}"):
            navigate("editor", name)
            st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Activity Config Editor
# ---------------------------------------------------------------------------

def page_editor():
    act_name = st.session_state.selected_activity
    is_new = act_name == "__new__"

    if is_new:
        cfg = {
            "response_type": "deep_link",
            "is_two_step": False,
            "pre_handler_ref": None,
            "post_handler_ref": None,
            "pre_validation_rules": None,
            "post_validation_rules": None,
            "response_config": {},
            "integration_config": None,
            "pre_entity_updates": None,
            "post_entity_updates": None,
            "use_legacy_script": False,
        }
        display_name = ""
    else:
        cfg = st.session_state.activities.get(act_name, {})
        display_name = act_name

    # --- Back button ---
    if st.button("< Back to Activity List"):
        navigate("list")
        st.rerun()

    st.markdown(f"## {'New Activity' if is_new else act_name}")

    # Two-column layout: form (left) + JSON preview (right)
    left, right = st.columns([3, 2])

    with left:
        # ==================== SECTION 1: Basic Info ====================
        st.markdown("### Basic Info")

        if is_new:
            display_name = st.text_input("Activity Name", value="", key="ed_name")
        else:
            st.text_input("Activity Name", value=display_name, disabled=True, key="ed_name")

        bc1, bc2 = st.columns(2)
        response_type = bc1.selectbox(
            "Response Type",
            RESPONSE_TYPES,
            index=RESPONSE_TYPES.index(cfg["response_type"]) if cfg["response_type"] in RESPONSE_TYPES else 0,
            key="ed_rt",
        )
        cfg["response_type"] = response_type

        bc2_col1, bc2_col2 = bc2.columns(2)
        is_two_step = bc2_col1.toggle("Two-Step", value=cfg["is_two_step"], key="ed_twostep")
        cfg["is_two_step"] = is_two_step

        use_legacy = bc2_col2.toggle("Legacy Script", value=cfg.get("use_legacy_script", False), key="ed_legacy")
        cfg["use_legacy_script"] = use_legacy

        if use_legacy:
            st.warning("Legacy script mode enabled. The resolver will forward this activity to the sandbox. All config below is ignored at runtime.")

        st.divider()

        # ==================== SECTION 2: Handlers ====================
        with st.expander("Handlers", expanded=True):
            # Pre handler
            pre_ref = cfg.get("pre_handler_ref")
            if pre_ref is None:
                pre_idx = 0
            elif pre_ref in PRE_HANDLERS:
                pre_idx = PRE_HANDLERS.index(pre_ref)
            else:
                pre_idx = len(PRE_HANDLERS) - 1  # custom

            pre_handler = st.selectbox("Pre Handler", PRE_HANDLERS, index=pre_idx, key="ed_pre_h")

            if pre_handler == "Generic (auto-resolved by response_type)":
                cfg["pre_handler_ref"] = None
                generic_name = GENERIC_PRE_MAP.get(response_type, "?")
                st.info(f"Auto-resolved: `{response_type}` -> **{generic_name}**")
            elif pre_handler == "+ Custom (enter class name)":
                custom_val = st.text_input("Custom Pre Handler Class", value=pre_ref or "", key="ed_pre_custom")
                cfg["pre_handler_ref"] = custom_val if custom_val else None
            else:
                cfg["pre_handler_ref"] = pre_handler

            # Post handler (only when two-step)
            if is_two_step:
                post_ref = cfg.get("post_handler_ref")
                if post_ref is None:
                    post_idx = 0
                elif post_ref in POST_HANDLERS:
                    post_idx = POST_HANDLERS.index(post_ref)
                else:
                    post_idx = len(POST_HANDLERS) - 1

                post_handler = st.selectbox("Post Handler", POST_HANDLERS, index=post_idx, key="ed_post_h")

                if post_handler == "GenericToastPostHandler (default)":
                    cfg["post_handler_ref"] = None
                    st.info("Default: **GenericToastPostHandler** -- returns success/cancelled toast")
                elif post_handler == "+ Custom (enter class name)":
                    custom_val = st.text_input("Custom Post Handler Class", value=post_ref or "", key="ed_post_custom")
                    cfg["post_handler_ref"] = custom_val if custom_val else None
                else:
                    cfg["post_handler_ref"] = post_handler
            else:
                cfg["post_handler_ref"] = None

        # ==================== SECTION 3: Validation Rules ====================
        _render_validation_section("Pre Validation Rules", "pre_validation_rules", cfg)

        if is_two_step:
            _render_validation_section("Post Validation Rules", "post_validation_rules", cfg)

        # ==================== SECTION 4: Response Config ====================
        with st.expander("Response Config", expanded=True):
            _render_response_config(cfg, response_type, is_two_step)

        # ==================== SECTION 5: Entity Updates ====================
        _render_entity_updates_section(
            "Pre-Handler Entity Updates (Step 6A: after validation, before handler)",
            "pre_entity_updates", cfg,
        )
        _render_entity_updates_section(
            "Post-Handler Entity Updates (Step 7A: after handler, before integrations)",
            "post_entity_updates", cfg,
        )

        # ==================== SECTION 6: Integration Pipeline ====================
        with st.expander("Integration Pipeline", expanded=True):
            _render_integration_pipeline(cfg)

    # --- Right panel: JSON preview ---
    with right:
        st.markdown("### Live JSON Preview")
        json_str = build_config_json(display_name, cfg)
        st.code(json_str, language="json")

    # --- Save ---
    if not is_new:
        st.session_state.activities[act_name] = cfg


# ---------------------------------------------------------------------------
# Validation Rules UI
# ---------------------------------------------------------------------------

def _render_validation_section(title: str, key: str, cfg: dict):
    with st.expander(title, expanded=False):
        rules_lib = st.session_state.validation_rules
        rule_names = list(rules_lib.keys())

        current_rules = cfg.get(key) or []
        current_names = [_rule_name(r) for r in current_rules]

        selected = st.multiselect(
            f"Select rules from library",
            rule_names,
            default=[n for n in current_names if n in rule_names],
            key=f"ms_{key}",
        )

        new_rules = []
        for rule_name in selected:
            existing = None
            for r in current_rules:
                if _rule_name(r) == rule_name:
                    existing = r
                    break

            lib_rule = rules_lib[rule_name]

            with st.container(border=True):
                st.markdown(f"**{rule_name}**")
                st.code(lib_rule["expression"], language="javascript")

                has_override = isinstance(existing, dict) and existing.get("rule")
                use_default = st.checkbox(
                    "Use defaults",
                    value=not has_override,
                    key=f"def_{key}_{rule_name}",
                )

                if use_default:
                    new_rules.append(rule_name)
                else:
                    oc1, oc2 = st.columns(2)
                    override_title = oc1.text_input(
                        "Error Title",
                        value=existing.get("error_title", lib_rule["error_title"]) if isinstance(existing, dict) else lib_rule["error_title"],
                        key=f"ot_{key}_{rule_name}",
                    )
                    override_sub = oc2.text_input(
                        "Error Subtitle",
                        value=existing.get("error_subtitle", lib_rule["error_subtitle"]) if isinstance(existing, dict) else lib_rule["error_subtitle"],
                        key=f"os_{key}_{rule_name}",
                    )
                    cur_toast = existing.get("error_toast_type", lib_rule["error_toast_type"]) if isinstance(existing, dict) else lib_rule["error_toast_type"]
                    override_toast = st.selectbox(
                        "Toast Type",
                        TOAST_TYPES,
                        index=TOAST_TYPES.index(cur_toast) if cur_toast in TOAST_TYPES else 0,
                        key=f"tt_{key}_{rule_name}",
                    )
                    entry = {"rule": rule_name, "error_title": override_title, "error_subtitle": override_sub, "error_toast_type": override_toast}
                    new_rules.append(entry)

        cfg[key] = new_rules if new_rules else None


# ---------------------------------------------------------------------------
# Response Config UI (morphs by response_type)
# ---------------------------------------------------------------------------

def _render_response_config(cfg: dict, response_type: str, is_two_step: bool):
    rc = cfg.get("response_config") or {}

    if response_type in ("deep_link", "phone_call"):
        rc["url_template"] = st.text_input(
            "URL Template",
            value=rc.get("url_template", ""),
            key="rc_url",
            help="Use {variable} syntax, e.g. {company_url}/app/#/page",
        )
        st.caption("Available: `{company_url}`, `{lead_id}`, `{product_data.data.*}`, `{lead_summary.data.*}`, `{correlation_id}`, `{activity_id}`")
        rc["display_text"] = st.text_input("Display Text", value=rc.get("display_text", ""), key="rc_dt")
        if is_two_step:
            r1, r2 = st.columns(2)
            rc["success_title"] = r1.text_input("Success Title", value=rc.get("success_title", ""), key="rc_st")
            rc["success_subtitle"] = r2.text_input("Success Subtitle", value=rc.get("success_subtitle", ""), key="rc_ss")

    elif response_type == "form_input":
        rc["popup_title"] = st.text_input("Popup Title", value=rc.get("popup_title", ""), key="rc_pt")
        fc1, fc2, fc3 = st.columns(3)
        rc["success_button_label"] = fc1.text_input("Submit Button", value=rc.get("success_button_label", "Submit"), key="rc_sbl")
        rc["cancel_button_label"] = fc2.text_input("Cancel Button", value=rc.get("cancel_button_label", "Cancel"), key="rc_cbl")
        rc["close_button_visible"] = fc3.toggle("Close Button", value=rc.get("close_button_visible", True), key="rc_cbv")
        rc["display_text"] = st.text_input("Display Text", value=rc.get("display_text", ""), key="rc_dt")
        fc4, fc5 = st.columns(2)
        rc["success_title"] = fc4.text_input("Success Title", value=rc.get("success_title", ""), key="rc_st")
        rc["success_subtitle"] = fc5.text_input("Success Subtitle", value=rc.get("success_subtitle", ""), key="rc_ss")

        # Form fields builder
        st.markdown("#### Form Fields")
        fields = rc.get("fields", [])
        new_fields = []
        for i, field in enumerate(fields):
            with st.container(border=True):
                hc1, hc2, hc3 = st.columns([3, 3, 1])
                field["name"] = hc1.text_input("Field Name", value=field.get("name", ""), key=f"ff_n_{i}")
                field["label"] = hc2.text_input("Label", value=field.get("label", ""), key=f"ff_l_{i}")
                remove = hc3.button("Remove", key=f"ff_rm_{i}")
                if remove:
                    continue

                fc1, fc2, fc3 = st.columns(3)
                field["type"] = fc1.selectbox(
                    "Type", FIELD_TYPES,
                    index=FIELD_TYPES.index(field.get("type", "text")) if field.get("type", "text") in FIELD_TYPES else 0,
                    key=f"ff_t_{i}",
                )
                field["required"] = fc2.toggle("Required", value=field.get("required", False), key=f"ff_r_{i}")

                if field["type"] == "text":
                    field["regex"] = fc3.text_input("Regex", value=field.get("regex", ""), key=f"ff_rx_{i}")
                elif field["type"] == "dropdown":
                    src = field.get("options_source", "products_list")
                    idx = OPTIONS_SOURCES.index(src) if src in OPTIONS_SOURCES else len(OPTIONS_SOURCES) - 1
                    field["options_source"] = fc3.selectbox("Options Source", OPTIONS_SOURCES, index=idx, key=f"ff_os_{i}")

                new_fields.append(field)

        if st.button("+ Add Field", key="ff_add"):
            new_fields.append({"name": "", "label": "", "type": "text", "required": False})
        rc["fields"] = new_fields

    elif response_type == "confirmation_popup":
        rc["popup_title"] = st.text_input("Popup Title", value=rc.get("popup_title", ""), key="rc_pt")
        rc["popup_subtitle"] = st.text_input("Popup Subtitle", value=rc.get("popup_subtitle", ""), key="rc_ps")
        rc["description"] = st.text_area("Description", value=rc.get("description", ""), key="rc_desc")
        fc1, fc2 = st.columns(2)
        rc["success_button_label"] = fc1.text_input("Confirm Button", value=rc.get("success_button_label", "Confirm"), key="rc_sbl")
        rc["cancel_button_label"] = fc2.text_input("Cancel Button", value=rc.get("cancel_button_label", "Cancel"), key="rc_cbl")
        rc["display_text"] = st.text_input("Display Text", value=rc.get("display_text", ""), key="rc_dt")
        fc3, fc4 = st.columns(2)
        rc["success_title"] = fc3.text_input("Success Title", value=rc.get("success_title", ""), key="rc_st")
        rc["success_subtitle"] = fc4.text_input("Success Subtitle", value=rc.get("success_subtitle", ""), key="rc_ss")

    elif response_type == "toast":
        rc["display_text"] = st.text_input("Display Text", value=rc.get("display_text", ""), key="rc_dt")
        tc1, tc2 = st.columns(2)
        rc["success_title"] = tc1.text_input("Success Title", value=rc.get("success_title", ""), key="rc_st")
        rc["success_subtitle"] = tc2.text_input("Success Subtitle", value=rc.get("success_subtitle", ""), key="rc_ss")

    cfg["response_config"] = rc


# ---------------------------------------------------------------------------
# Integration Pipeline UI
# ---------------------------------------------------------------------------

def _render_integration_pipeline(cfg: dict):
    integrations = cfg.get("integration_config") or []
    int_count = len(integrations)

    if int_count > 0:
        st.markdown(
            f'{badge(f"{int_count} integration{"s" if int_count > 1 else ""} configured", "#546E7A")}',
            unsafe_allow_html=True,
        )
    else:
        st.caption("No integrations configured")

    new_integrations = []
    for i, intg in enumerate(integrations):
        phase_color = "#1565C0" if intg.get("phase") == "pre" else "#2E7D32"
        with st.container(border=True):
            st.markdown(
                f'<div style="border-left:4px solid {phase_color};padding-left:8px;">'
                f'<strong>#{i + 1}</strong> &nbsp; {badge(intg.get("phase", "pre").upper(), phase_color)} '
                f'&nbsp; <code>{intg.get("event", "")}</code></div>',
                unsafe_allow_html=True,
            )

            ic1, ic2, ic3, ic4 = st.columns(4)
            intg["event"] = ic1.selectbox(
                "Event", INTEGRATION_EVENTS,
                index=INTEGRATION_EVENTS.index(intg["event"]) if intg.get("event") in INTEGRATION_EVENTS else 0,
                key=f"int_ev_{i}",
            )
            intg["phase"] = ic2.selectbox(
                "Phase", INTEGRATION_PHASES,
                index=INTEGRATION_PHASES.index(intg.get("phase", "pre")),
                key=f"int_ph_{i}",
            )
            intg["trigger"] = ic3.selectbox(
                "Trigger", INTEGRATION_TRIGGERS,
                index=INTEGRATION_TRIGGERS.index(intg.get("trigger", "on_success")),
                key=f"int_tr_{i}",
            )
            intg["mode"] = ic4.selectbox(
                "Mode", INTEGRATION_MODES,
                index=INTEGRATION_MODES.index(intg.get("mode", "blocking")),
                key=f"int_mo_{i}",
            )

            mc1, mc2, mc3 = st.columns([1, 3, 1])
            if intg.get("mode") == "blocking":
                intg["fail_on_error"] = mc1.toggle("Fail on Error", value=intg.get("fail_on_error", False), key=f"int_fe_{i}")
            else:
                mc1.toggle("Fail on Error", value=False, disabled=True, key=f"int_fe_{i}")
                intg["fail_on_error"] = False

            intg["condition"] = mc2.text_input(
                "Condition (JSONata)",
                value=intg.get("condition", ""),
                placeholder="e.g. payload.is_submitted = true",
                key=f"int_cond_{i}",
            )
            if not intg.get("condition"):
                intg.pop("condition", None)

            remove = mc3.button("Remove", key=f"int_rm_{i}")
            if remove:
                continue

            params_str = json.dumps(intg.get("params", {}), indent=2)
            params_edited = st.text_area("Params (JSON)", value=params_str, height=80, key=f"int_params_{i}")
            try:
                intg["params"] = json.loads(params_edited)
            except json.JSONDecodeError:
                st.error("Invalid JSON in params")

            new_integrations.append(intg)

    if st.button("+ Add Integration", key="int_add"):
        new_integrations.append({
            "event": "lsq_create_activity",
            "phase": "post",
            "trigger": "on_success",
            "mode": "blocking",
            "fail_on_error": False,
            "params": {},
        })

    cfg["integration_config"] = new_integrations if new_integrations else None


# ---------------------------------------------------------------------------
# Entity Updates UI
# ---------------------------------------------------------------------------

def _render_entity_updates_section(title: str, key: str, cfg: dict):
    with st.expander(title, expanded=False):
        rules = cfg.get(key) or []
        rule_count = len(rules)

        if rule_count > 0:
            st.markdown(
                f'{badge(f"{rule_count} update rule{"s" if rule_count > 1 else ""}", "#6A1B9A")}',
                unsafe_allow_html=True,
            )
            st.caption("Rules execute sequentially. If source_expression evaluates to null, the rule is skipped.")
        else:
            st.caption("No entity update rules configured")

        new_rules = []
        for i, rule in enumerate(rules):
            entity_color = "#6A1B9A"
            with st.container(border=True):
                st.markdown(
                    f'<div style="border-left:4px solid {entity_color};padding-left:8px;">'
                    f'<strong>#{i + 1}</strong> &nbsp; '
                    f'{badge(rule.get("entity", "Lead"), entity_color)} '
                    f'&nbsp; <code>{rule.get("destination_property", "")}</code></div>',
                    unsafe_allow_html=True,
                )

                ec1, ec2 = st.columns(2)
                rule["entity"] = ec1.selectbox(
                    "Target Entity",
                    ENTITY_TYPES,
                    index=ENTITY_TYPES.index(rule.get("entity", "Lead")) if rule.get("entity", "Lead") in ENTITY_TYPES else 0,
                    key=f"eu_{key}_ent_{i}",
                )
                default_id = ENTITY_ID_HINTS.get(rule["entity"], "lead_id")
                rule["identifier"] = ec2.text_input(
                    "Identifier (JSONata)",
                    value=rule.get("identifier", default_id),
                    placeholder=f"e.g. {default_id}",
                    key=f"eu_{key}_id_{i}",
                    help="JSONata expression that resolves to the entity PK (UUID)",
                )

                rule["source_expression"] = st.text_input(
                    "Source Expression (JSONata)",
                    value=rule.get("source_expression", ""),
                    placeholder="e.g. handler_result.payload.proposal_number or 'verified'",
                    key=f"eu_{key}_src_{i}",
                    help="JSONata expression evaluated against ctx. The result is the value to write.",
                )

                dc1, dc2, dc3 = st.columns([3, 2, 1])
                rule["destination_property"] = dc1.text_input(
                    "Destination Property",
                    value=rule.get("destination_property", ""),
                    placeholder="e.g. verification_status",
                    key=f"eu_{key}_dst_{i}",
                    help="System field = direct DB update. Custom field = via CustomFieldsManager.",
                )

                sys_fields = ENTITY_SYSTEM_FIELDS.get(rule["entity"], [])
                dest = rule.get("destination_property", "")
                if dest and sys_fields:
                    if dest in sys_fields:
                        dc2.success("System field")
                    else:
                        dc2.info("Custom field")
                elif dest and not sys_fields:
                    dc2.info("Custom field")

                remove = dc3.button("Remove", key=f"eu_{key}_rm_{i}")
                if remove:
                    continue

                new_rules.append(rule)

        if st.button("+ Add Entity Update Rule", key=f"eu_{key}_add"):
            new_rules.append({
                "source_expression": "",
                "entity": "Lead",
                "identifier": "lead_id",
                "destination_property": "",
            })

        cfg[key] = new_rules if new_rules else None


# ---------------------------------------------------------------------------
# Page 3: Validation Rule Library
# ---------------------------------------------------------------------------

def page_validation_rules():
    st.markdown("## Validation Rule Library")
    st.caption("Reusable validation rules referenced by activities. Backed by the `validation_rule` table.")

    rules = st.session_state.validation_rules

    # Stats
    total_rules = len(rules)
    activities = st.session_state.activities
    usage_counts = {}
    for rname in rules:
        count = 0
        for cfg in activities.values():
            for key in ("pre_validation_rules", "post_validation_rules"):
                for r in (cfg.get(key) or []):
                    if _rule_name(r) == rname:
                        count += 1
        usage_counts[rname] = count

    c1, c2 = st.columns(2)
    c1.metric("Total Rules", total_rules)
    c2.metric("Total Usages", sum(usage_counts.values()))

    st.divider()

    # --- Table header ---
    cols = st.columns([2, 3, 2, 2, 1, 1])
    cols[0].markdown("**Name**")
    cols[1].markdown("**Expression**")
    cols[2].markdown("**Error Title**")
    cols[3].markdown("**Error Subtitle**")
    cols[4].markdown("**Toast**")
    cols[5].markdown("**Used**")
    st.divider()

    for rname, rule in rules.items():
        cols = st.columns([2, 3, 2, 2, 1, 1])
        cols[0].markdown(f"`{rname}`")
        cols[1].code(rule["expression"], language=None)
        cols[2].markdown(rule["error_title"])
        cols[3].markdown(rule["error_subtitle"] or "--")
        cols[4].markdown(badge(rule["error_toast_type"], BADGE_COLORS.get(rule["error_toast_type"], "#E53935")), unsafe_allow_html=True)
        usage = usage_counts.get(rname, 0)
        cols[5].markdown(f"**{usage}** activities")

    st.divider()

    # --- Add new rule ---
    st.markdown("### Add New Rule")
    with st.form("add_rule_form"):
        nc1, nc2 = st.columns(2)
        new_name = nc1.text_input("Rule Name", placeholder="e.g. lead_has_email")
        new_expr = nc2.text_input("JSONata Expression", placeholder='$exists(lead_summary.data.contact.email)')
        nc3, nc4, nc5 = st.columns(3)
        new_title = nc3.text_input("Error Title", value="Action failed")
        new_sub = nc4.text_input("Error Subtitle", value="")
        new_toast = nc5.selectbox("Toast Type", TOAST_TYPES)

        submitted = st.form_submit_button("Add Rule")
        if submitted and new_name and new_expr:
            st.session_state.validation_rules[new_name] = {
                "name": new_name,
                "expression": new_expr,
                "error_title": new_title,
                "error_subtitle": new_sub,
                "error_toast_type": new_toast,
            }
            st.success(f"Rule `{new_name}` added.")
            st.rerun()

    # --- Test rule ---
    st.divider()
    st.markdown("### Test a Rule")
    st.caption("Paste a sample context JSON and pick a rule to evaluate.")
    tc1, tc2 = st.columns([3, 1])
    test_json = tc1.text_area("Sample Context (JSON)", value='{\n  "lead_summary": {\n    "data": {\n      "contact": {\n        "primary_mobile_number": "9876543210"\n      }\n    }\n  }\n}', height=150, key="test_ctx")
    test_rule = tc2.selectbox("Rule to test", list(rules.keys()), key="test_rule_sel")
    if tc2.button("Evaluate"):
        rule_expr = rules[test_rule]["expression"]
        st.info(f"Expression: `{rule_expr}`")
        st.warning("JSONata evaluation requires the `jsonata-python` package (not included in this wireframe). In the real admin panel, this would evaluate the expression against the sample context and show pass/fail.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Activity Config Admin",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_state()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("# Activity Admin")
        st.divider()

        if st.button("Activity List", use_container_width=True, type="primary" if st.session_state.current_page == "list" else "secondary"):
            navigate("list")
            st.rerun()

        if st.button("Validation Rules", use_container_width=True, type="primary" if st.session_state.current_page == "rules" else "secondary"):
            navigate("rules")
            st.rerun()

        st.divider()
        st.caption(f"{len(st.session_state.activities)} activities configured")
        st.caption(f"{len(st.session_state.validation_rules)} validation rules")

    # Page router
    page = st.session_state.current_page
    if page == "list":
        page_activity_list()
    elif page == "editor":
        page_editor()
    elif page == "rules":
        page_validation_rules()
    else:
        page_activity_list()


if __name__ == "__main__":
    main()
