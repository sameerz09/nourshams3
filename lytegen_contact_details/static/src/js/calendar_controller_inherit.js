/** @odoo-module **/

import { CalendarController } from '@web/views/calendar/calendar_controller';

export class CustomCalendarController extends CalendarController {
    setup() {
        super.setup();
        console.log("Custom Calendar Controller loaded!");

        // Add your custom logic here
        this.customMethod();
    }

    customMethod() {
        console.log("Custom method executed!");
        // Add your custom code here
    }
}
