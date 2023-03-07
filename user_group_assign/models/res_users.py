from odoo import api, fields, models
from odoo.exceptions import ValidationError, AccessError
from odoo.addons.base.models.res_users import is_selection_groups, get_selection_groups
from itertools import chain


class ResUsers(models.Model):
    _inherit = 'res.users'

    show_user_access = fields.Boolean(compute='_compute_show_user_access')
    user_manager_ids = fields.Many2many('res.users', 'rel_access_control_user_manager', 'managed_user', 'manager', string="Managed by",
                                        default=lambda x: x.env.user.ids + x.env.user.user_manager_ids.ids, groups='base.group_system',
                                        domain="[('groups_id', 'ilike', 'Administration / Access Rights'), ('id', '!=', id), ('id', 'not in', manager_of_ids)]",
                                        help="These selected managers are allowed to change the permissions of this user")
    manager_of_ids = fields.Many2many('res.users', 'rel_access_control_user_manager', 'manager', 'managed_user', string="Manager of",
                                      groups='base.group_system', domain="[('id', '!=', id), ('id', 'not in', user_manager_ids)]")
    assignable_groups_inherit = fields.Boolean("Control Inherited Groups", default=True, groups='base.group_system',
                                               help="Choose the groups the user is allowed to modify.\n"
                                                    "Administrators (with group 'Settings') bypass this setting and have full write access")
    assignable_groups_domain = fields.Many2many(related='groups_id', string="Assignable Groups Domain")
    assignable_group_ids = fields.Many2many('res.groups', 'rel_user_groups_assignable', string="Controllable Groups", groups='base.group_system',
                                            domain="[('id', 'in', assignable_groups_domain)]",
                                            help="Allow user to adjust other user's access rights, "
                                                 "as long as those rights are not greater than the user's."
                                                 "Administrators (with group 'Settings') bypass this setting and have full write access")

    @api.model
    def check_assignable_groups(self, vals, create=False):
        if not self.env.is_system():
            user = self.env.user
            editing_self = self == self.env.user
            if not create and user not in self.sudo().user_manager_ids and not editing_self:
                raise AccessError("The user cannot be modified due to security restrictions.\n\n"
                                  "You are not a manager of this user, please contact your administrator.")

            modified_group_fields = set(filter(is_selection_groups, vals.keys()))

            # Get all possible groups the user is modifying
            original_groups = set(chain.from_iterable(get_selection_groups(f) for f in modified_group_fields)) & set(self.groups_id.ids)
            write_groups = list(set(vals[f] for f in modified_group_fields) | original_groups)

            # Get all groups (as well as their inherited groups) that the user is allowed to modify
            allowed_groups = set(user.groups_id.ids if user.assignable_groups_inherit else user._origin.assignable_group_ids.ids)
            allowed_groups |= set(self.env['res.groups'].browse(allowed_groups).implied_ids.ids)

            invalid_groups = set(filter(bool, write_groups)) - set(filter(bool, allowed_groups))
            if invalid_groups:
                names = self.env['res.groups'].browse(invalid_groups).mapped('name')
                raise AccessError(f"The requested groups cannot be assigned/removed due to security restrictions:\n\n{', '.join(names)}")

    @api.model
    def create(self, vals):
        self.check_assignable_groups(vals, True)
        return super().create(vals)

    def write(self, vals):
        self.check_assignable_groups(vals)
        return super().write(vals)

    @api.onchange('assignable_group_ids', 'groups_id')
    @api.constrains('assignable_group_ids', 'groups_id')
    def _constrain_assignable_group_ids(self):
        """ Ensure a user cannot create another user with higher access rights """
        for user in self.sudo().filtered(lambda x: not x.assignable_groups_inherit):
            invalid_groups = user.assignable_group_ids - user.groups_id
            if invalid_groups:
                names = invalid_groups.mapped('name')
                raise ValidationError(f"User cannot assign groups with higher access rights than themselves:\n\n{', '.join(names)}")

    @api.depends('groups_id')
    def _compute_show_user_access(self):
        access_group = self.env.ref('base.group_system')
        for user in self:
            user.show_user_access = access_group in self.env.user.groups_id
