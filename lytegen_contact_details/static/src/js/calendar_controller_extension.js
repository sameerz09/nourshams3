/** @odoo-module **/

import { registry } from '@web/core/registry';
import { CustomCalendarController } from './calendar_controller_inherit';

registry.category('views').add('calendar_controller', CustomCalendarController);
