from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging

_logger = logging.getLogger(__name__)

class PortalAppointment(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'appointment_count' in counters:
            # Search for appointments where customer is partner OR attendee
            domain = [
                '|',
                ('partner_id', '=', partner.id),
                ('attendee_ids.partner_id', '=', partner.id)
            ]
            values['appointment_count'] = request.env['calendar.event'].sudo().search_count(domain)
        
        return values

    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        CalendarEvent = request.env['calendar.event']

        # Domain to find customer's appointments
        domain = [
            '|',
            ('partner_id', '=', partner.id),
            ('attendee_ids.partner_id', '=', partner.id)
        ]
        
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'start desc'},
            'name': {'label': 'Title', 'order': 'name'},
        }

        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'upcoming': {'label': 'Upcoming', 'domain': [('start', '>=', fields.Datetime.now())]},
            'past': {'label': 'Past', 'domain': [('start', '<', fields.Datetime.now())]},
        }

        # Set defaults
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
            
        order = searchbar_sortings[sortby]['order']

        # Apply filters
        if filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']

        # Apply search
        if search and search_in:
            if search_in in ('all', 'name'):
                domain += [('name', 'ilike', search)]

        # Apply date range
        if date_begin and date_end:
            domain += [('start', '>=', date_begin), ('start', '<=', date_end)]

        # Count for pager
        appointment_count = CalendarEvent.sudo().search_count(domain)

        # Pager
        pager = portal_pager(
            url="/my/appointments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=appointment_count,
            page=page,
            step=self._items_per_page
        )

        # Get appointments
        appointments = CalendarEvent.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'appointments': appointments,
            'page_name': 'appointments',
            'pager': pager,
            'default_url': '/my/appointments',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
        })
        
        return request.render("portal_appointments.portal_my_appointments", values)

    @http.route(['/debug/templates'], type='http', auth="user")
    def debug_templates(self):
        try:
            template = request.env.ref('portal_appointments.portal_my_appointments', False)
            return f"Template found: {template} - ID: {template.id if template else 'Not found'}"
        except Exception as e:
            return f"Error: {e}"
    
    @http.route(['/test/simple'], type='http', auth="public", website=True)
    def test_simple(self):
        return "Controller is working!"